from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy import ForeignKey, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import load_only
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from threading import Thread
from flask import Flask, request
from hashlib import sha256
from uuid import uuid4

import json

DatabaseBase = declarative_base()
app = Flask(__name__)
db_engine = create_engine('sqlite:///master.db', connect_args={'check_same_thread':False})
session_maker = sessionmaker()
session_maker.configure(bind=db_engine)

main_session = session_maker()

MAX_PAGINATION_SIZE = 50

#######################
## Route Definitions ##
#######################

#################
## User routes ##
#################
@app.route('/api/v1/users/authenticate', methods=['POST'])
def users_authenticate():
	user = request.form.get('username')
	password = request.form.get('password')

	matching_user = main_session.query(User).filter(User.username == user).one()
	hashed_password = sha256((matching_user.salt+password).encode("utf-8")).hexdigest()

	if (matching_user.password == hashed_password):
		# Generate Access token
		session = Session()
		session.id = new_uuid()
		session.userID = matching_user.id
		session.addressIssued = request.remote_addr
		# Delete existing access tokens
		matching_session = main_session.query(Session).filter(Session.userID == matching_user.id).first()
		if (matching_session != None):
			main_session.delete(matching_session)
		# Commit new token and return
		main_session.add(session)
		main_session.commit()
		return session.id
	else:
		return was403()

	return ("%s : %s"%(hashed_password, matching_user.password))

@app.route('/api/v1/users/logout', methods=['POST'])
def users_logout():
	session_id = request.headers["auth-id"]
	user = get_user_by_session(session_id)
	if (user != None):
		sessions = main_session.query(Session).filter(Session.userID == user.id).all()
		for session in sessions:
			main_session.delete(session)
		main_session.commit()
		return "Success"
	else:
		return was403()

@app.route('/api/v1/users/create', methods=['POST'])
def users_create():
	username = request.form.get('username')
	password = request.form.get('password')

	user = User()
	user.username = username
	user.salt = new_uuid()
	user.password = sha256((user.salt+password).encode("utf-8")).hexdigest()
	user.id = new_uuid()
	user.display_name = request.form.get('display_name')
	user.first_name = request.form.get('first_name')
	user.last_name = request.form.get('last_name')
	user.email = request.form.get('email')

	main_session.add(user)
	main_session.commit()

	return user.id

@app.route('/api/v1/users/update', methods=['POST'])
def users_update():
	session_id = request.headers["auth-id"]
	user = get_user_by_session(session_id)
	if (user != None):
		user.username = request.form.get('username')
		password = request.form.get('password')
		new_password = sha256((user.salt+password).encode("utf-8")).hexdigest()
		user.password = new_password
		user.display_name = request.form.get('display_name')
		user.first_name = request.form.get('first_name')
		user.last_name = request.form.get('last_name')
		user.email = request.form.get('email')

		main_session.commit()
	else:
		return was403()

@app.route('/api/v1/users/session', methods=['POST'])
def users_session_validate():
	#TODO: Add session expiration. Also validation by IP to prevent session hijacking
	session_id = request.headers["auth-id"]
	session_obj = main_session.query(Session).filter(Session.id == session_id).first()
	if session_obj != None:
		return "OK", 200
	else:
		return was403()

@app.route('/api/v1/users/get_username', methods=['GET'])
def users_get_username():
	session_id = request.headers["auth-id"]
	user = get_user_by_session(session_id)
	if (user != None):
		return user.username
	else:
		return was403()

#######################
## Credential Routes ##
#######################
"""@app.route('/api/v1/credentials/created_by_me', methods=['GET'])
def credentials_get_my():
	session_id = request.headers["auth-id"]
	user = get_user_by_session(session_id)
	if (user != None):
		created_by_creds = main_session.query(Credential).filter(Credential.createdByID == user.id).all()
		return json.dumps(created_by_creds, cls=PswdSafeAlchemyEncoder)
	else:
		return "Invalid session.", 403"""

@app.route('/api/v1/credentials/<string:cred_id>', methods=['GET'])
def credentials_get_specific(cred_id):
	session_id = request.headers["auth-id"]
	user = get_user_by_session(session_id)
	if (user != None):
		credPerm = main_session.query(CredentialPermission).filter(CredentialPermission.credentialID == cred_id).filter(CredentialPermission.userID == user.id).first()
		return json.dumps(credPerm.credential, cls=AlchemyEncoder)
	else:
		return was403()

@app.route('/api/v1/credentials/create', methods=['POST'])
def credentials_create():
	session_id = request.headers["auth-id"]
	user = get_user_by_session(session_id)
	if (user != None):
		cred = Credential()
		cred.id = new_uuid()
		cred.username = get_value_or_blank(request, "username")
		cred.password = get_value_or_blank(request, "password")
		cred.target = get_value_or_blank(request, "target")
		cred.notes = get_value_or_blank(request, "notes")
		cred.displayName = get_value_or_blank(request, "displayName")
		cred.permissionID = new_uuid()
		cred.createdByID = user.id

		credPerm = CredentialPermission()
		credPerm.id = new_uuid()
		credPerm.credentialID = cred.id
		credPerm.userID = user.id

		main_session.add(cred)
		main_session.add(credPerm)

		main_session.commit()
		return cred.id
	else:
		return was403()

@app.route('/api/v1/credentials/update', methods=['POST'])
def credentials_update():
	session_id = request.headers["auth-id"]
	user = get_user_by_session(session_id)
	if (user != None):
		credentialID = request.form.get('id')
		credPerm = main_session.query(CredentialPermission).filter(CredentialPermission.credentialID == credentialID).filter(CredentialPermission.userID == user.id).first()
		if (credPerm != None):
			cred = credPerm.credential
			cred.username = get_value_or_blank(request, "username")
			cred.password = get_value_or_blank(request, "password")
			cred.target = get_value_or_blank(request, "target")
			cred.notes = get_value_or_blank(request, "notes")
			cred.displayName = get_value_or_blank(request, "displayName")

			main_session.commit()
			return cred.id
		else:
			return was500()
	else:
		return was403()

@app.route('/api/v1/credentials/delete', methods=['POST'])
def credentials_delete():
	session_id = request.headers["auth-id"]
	user = get_user_by_session(session_id)
	if (user != None):
		credentialID = request.form.get('credential_id')
		credPerm = main_session.query(CredentialPermission).filter(CredentialPermission.id == credentialID).filter(CredentialPermission.userID == user.id).first()
		if (credPerm != None):
			main_session.delete(credPerm)
			main_session.commit()
			return "Success"
		else:
			return was500()
	else:
		return was403()

@app.route('/api/v1/credentials/all/<int:page_num>&<int:limit>', methods=['GET'])
def credentials_get_page(page_num, limit):
	if (limit > MAX_PAGINATION_SIZE):
		return was500("Invalid page limit")
	session_id = request.headers["auth-id"]
	user = get_user_by_session(session_id)
	if (user != None):
		credentials_with_permission = main_session.query(CredentialPermission).filter(CredentialPermission.userID == user.id).order_by(CredentialPermission.id.desc())
		item_count = credentials_with_permission.count()
		credentials_with_permission = credentials_with_permission.offset(page_num*limit).limit(limit)
		returnList = []
		for credPerm in credentials_with_permission:
			returnList.append(credPerm.credential)
		returnItem = {"count":item_count, "data":returnList}
		return json.dumps(returnItem, cls=PswdSafeAlchemyEncoder)
	else:
		return was403()

@app.route('/api/v1/credentials/all/search/<string:query>/<int:page_num>&<int:limit>', methods=['GET'])
def credentials_get_query_page(query, page_num, limit):
	##Inefficient search algo
	##needs to update
	if (limit > MAX_PAGINATION_SIZE):
		return was500("Invalid page limit")
	session_id = request.headers["auth-id"]
	user = get_user_by_session(session_id)
	if (user != None):
		credentials_with_permission = main_session.query(CredentialPermission).filter(CredentialPermission.userID == user.id).order_by(CredentialPermission.id.desc())
		returnList = []
		for credPerm in credentials_with_permission:
			if (query.lower() in credPerm.credential.username.lower()):
				returnList.append(credPerm.credential)
				continue
			elif (query.lower() in credPerm.credential.password.lower()):
				returnList.append(credPerm.credential)
				continue
			elif (query.lower() in credPerm.credential.notes.lower()):
				returnList.append(credPerm.credential)
				continue
			elif (query.lower() in credPerm.credential.target.lower()):
				returnList.append(credPerm.credential)
				continue
			elif (query.lower() in credPerm.credential.displayName.lower()):
				returnList.append(credPerm.credential)
				continue
		sub_query = returnList[(page_num*limit):((page_num*limit)+limit)]
		returnItem = {"count":len(returnList), "data":sub_query}
		return json.dumps(returnItem, cls=PswdSafeAlchemyEncoder)
	else:
		return was403()



##################
## Notes Routes ##
##################

@app.route('/api/v1/notes/notebooks/delete', methods=['POST'])
def notebooks_delete():
	session_id = request.headers["auth-id"]
	user = get_user_by_session(session_id)
	if (user != None):
		notebookID = get_value_or_blank(request, "notebookID")
		notebook = main_session.query(Notebook).filter(Notebook.id == notebookID).one()
		if notebook != None:
			permission = main_session.query(NoteAccess).filter(NoteAccess.permissionID == notebook.permissionID).filter(NoteAccess.userID == user.id).one()
			if permission != None:
				pages = main_session.query(NotebookPage).filter(NotebookPage.notebook_id == notebook.id).all()
				for page in pages:
					local_creds = main_session.query(NoteAccess).filter(NoteAccess.permissionID == page.permissionID).all()
					for cred in local_creds:
						main_session.delete(cred)
					main_session.delete(page)

				creds = main_session.query(NoteAccess).filter(NoteAccess.permissionID == notebook.permissionID).all()
				for cred in creds:
					main_session.delete(cred)
				main_session.delete(notebook)
				main_session.commit()
				return "Success"
			else:
				return was403()
		else:
			return was500()
	else:
		return was403()
@app.route('/api/v1/notes/pages/delete', methods=['POST'])
def notepage_delete():
	session_id = request.headers["auth-id"]
	user = get_user_by_session(session_id)
	if (user != None):
		pageID = get_value_or_blank(request, "pageID")
		page = main_session.query(NotebookPage).filter(NotebookPage.id == pageID).one()
		if page != None:
			permission = main_session.query(NoteAccess).filter(NoteAccess.permissionID == page.permissionID).filter(NoteAccess.userID == user.id).one()
			if permission != None:
				main_session.delete(page)
				all_related_perms = main_session.query(NoteAccess).filter(NoteAccess.permissionID == page.permissionID).all()
				for perm in all_related_perms:
					main_session.delete(perm)
				main_session.commit()
				return "Success"
			else:
				return was403()
		else:
			return was500()
	else:
		return was403()

@app.route('/api/v1/notes/pages/update', methods=['POST'])
def notepage_save():
	session_id = request.headers["auth-id"]
	user = get_user_by_session(session_id)
	if (user != None):
		id = get_value_or_blank(request, "id")
		title = get_value_or_blank(request, "title")
		contents = get_value_or_blank(request, "content")

		notebookPage = main_session.query(NotebookPage).filter(NotebookPage.id == id).one()
		if (notebookPage != None):
			noteAccess = main_session.query(NoteAccess).filter(NoteAccess.userID == user.id).filter(NoteAccess.permissionID == notebookPage.permissionID).one()
			if (noteAccess != None):
				print(notebookPage.content, contents)
				notebookPage.title = title
				notebookPage.content = contents
				main_session.commit()
				return "Success"
			else:
				return was500()
		else:
			return was500()
	else:
		return was403();

@app.route('/api/v1/notes/notebook/all/<int:page_num>&<int:limit>', methods=['GET'])
def notebooks_get_all(page_num, limit):
	if (limit > MAX_PAGINATION_SIZE):
		return was500("Invalid page limit")
	session_id = request.headers["auth-id"]
	user = get_user_by_session(session_id)
	if (user != None):
		values_to_return = []
		permissions = main_session.query(NoteAccess).filter(NoteAccess.userID == user.id).filter(NoteAccess.type == "NOTEBOOK").all()
		for item in permissions:
			notebook = main_session.query(Notebook).filter(Notebook.permissionID == item.permissionID).one()
			values_to_return.append(notebook)
		sub_query = values_to_return[(page_num*limit):((page_num*limit)+limit)]
		returnVal = {"count":len(values_to_return), "data":sub_query}
		return json.dumps(returnVal, cls=AlchemyEncoder)
	return was403()

@app.route('/api/v1/notes/pages/by_notebook', methods=['POST'])
def notebooks_get_by_notebook():
	session_id = request.headers["auth-id"]
	user = get_user_by_session(session_id)
	if (user != None):
		values_to_return = []
		notebook_id = get_value_or_blank(request, "notebookID")
		if ("#" in notebook_id):
			notebook_id = notebook_id.replace("#", "")
		notebook = main_session.query(Notebook).filter(Notebook.id == notebook_id).first()
		if notebook != None:
			access_perms = main_session.query(NoteAccess).filter(NoteAccess.permissionID == notebook.permissionID).all()
			can_access_notebook = False
			for perm in access_perms:
				if perm.userID == user.id:
					can_access_notebook = True
					break
			if can_access_notebook:
				pages = main_session.query(NotebookPage).filter(NotebookPage.notebook_id == notebook.id).all()
				for page in pages:
					page_perms = main_session.query(NoteAccess).filter(NoteAccess.permissionID == page.permissionID).all()
					for perm in page_perms:
						if perm.userID == user.id:
							values_to_return.append(page)
				return json.dumps(values_to_return, cls=AlchemyEncoder)
			else:
				return was403()
		else:
			return was500()


# Add/Update page(s). Update notebook name. Create new notebook.
@app.route('/api/v1/notes/notebook/save', methods=['POST'])
def notebooks_save():
	session_id = request.headers["auth-id"]
	user = get_user_by_session(session_id)
	if (user != None):
		notebook_id = get_value_or_blank(request, "notebookID")
		if (notebook_id != ""):
			#Notebook exists. Do updates
			notebook = main_session.query(Notebook).filter(Notebook.id == notebook_id).first()
			notebookPermissions = main_session.query(NoteAccess).filter(NoteAccess.permissionID == Notebook.permissionID).all()
			can_access = False
			for perm in notebookPermissions:
				if (perm.userID == user.id):
					can_access = True
					break
			titleReturned = get_value_or_blank(request, "title")
			descReturned = get_value_or_blank(request, "desc")
			if (titleReturned != ""):
				notebook.title = titleReturned
			if (descReturned != ""):
				notebook.desc = descReturned
			pages = get_value_or_blank(request, "pages")
			created_pages = []
			if (len(pages) > 0):
				pages = json.loads(pages)
				for page in pages:
					pageJson = page
					try:
						page = main_session.query(NotebookPage).filter(NotebookPage.id == pageJson["id"]).filter(NotebookPage.notebook_id == notebook.id).first()
					except KeyError:
						page = None
					if (page != None):
						#Page exists. Check perms and update it.
						matching_pages_access = main_session.query(NoteAccess).filter(NoteAccess.permissionID == page.permissionID).all()
						for page_access in matching_pages_access:
							if page_access.userID == user.id:
								# You have all the correct perms to update this page.
								if ("content" in pageJson.keys()):
									page.content = pageJson["content"]
								page.title = pageJson["title"]
					else:
						noteAccessID = new_uuid()
						notepage = NotebookPage()
						notepage.id = new_uuid()
						notepage.createdByID = user.id
						notepage.permissionID = noteAccessID
						notepage.notebook_id = notebook.id
						notepage.content = pageJson["content"]
						notepage.title = pageJson["title"]

						notepageAccess = NoteAccess()
						notepageAccess.id = new_uuid()
						notepageAccess.userID = user.id
						notepageAccess.permissionID = noteAccessID
						notepageAccess.type = "NOTEBOOK_PAGE"
						main_session.add(notepage)
						main_session.add(notepageAccess)
						created_pages.append(notepage)
			main_session.commit()

			if (len(created_pages) != 0):
				return json.dumps(created_pages, cls=AlchemyEncoder)
			return "Success"
		else:
			#Notebook is new. Create it.
			notebookPermissionID = new_uuid()
			noteAccessID = new_uuid()

			notebook = Notebook()
			notebook.id = new_uuid()
			notebook.createdByID = user.id
			notebook.permissionID = notebookPermissionID
			notebook.title = get_value_or_blank(request, "title")
			notebook.desc = get_value_or_blank(request, "desc")

			notebookAccess = NoteAccess()
			notebookAccess.id = new_uuid()
			notebookAccess.userID = user.id
			notebookAccess.permissionID = notebookPermissionID
			notebookAccess.type = "NOTEBOOK"

			notepage = NotebookPage()
			notepage.id = new_uuid()
			notepage.notebook_id = notebook.id
			notepage.createdByID = user.id
			notepage.permissionID = noteAccessID
			notepage.content = ""
			notepage.title = "New notebook"

			notepageAccess = NoteAccess()
			notepageAccess.id = new_uuid()
			notepageAccess.userID = user.id
			notepageAccess.permissionID = noteAccessID
			notepageAccess.type = "NOTEBOOK_PAGE"

			main_session.add(notebook)
			main_session.add(notebookAccess)
			main_session.add(notepage)
			main_session.add(notepageAccess)

			main_session.commit()

			return notebook.id
	else:
		return was403()

@app.route('/api/v1/notes/notebook/search/<string:query>/<int:page_num>&<int:limit>', methods=['GET'])
def notebooks_search(query, page_num, limit):
	session_id = request.headers["auth-id"]
	user = get_user_by_session(session_id)
	if (user != None):
		perms = main_session.query(NoteAccess).filter(NoteAccess.userID == user.id).filter(NoteAccess.type == "NOTEBOOK").all()
		notebooks = []
		for perm in perms:
			print(perm.permissionID)
			notebook = main_session.query(Notebook).filter(Notebook.permissionID == perm.permissionID).one()
			#notebook = main_session.query(Notebook).filter(Notebook.permissionID == perm.permissionID).one()
			if query.lower() in notebook.title.lower():
				notebooks.append(notebook)
			elif query.lower() in notebook.desc.lower():
				notebooks.append(notebook)
		sub_query = notebooks[(page_num*limit):((page_num*limit)+limit)]
		returnItem = {"count":len(notebooks), "data":sub_query}
		return json.dumps(returnItem, cls=AlchemyEncoder)
	else:
		return was403()

#######################
## Utility Functions ##
#######################
def new_uuid():
	return str(uuid4())

def get_user_by_session(session):
	matching_session = main_session.query(Session).filter(Session.id == session).first()
	if (matching_session != None):
		user = main_session.query(User).filter(User.id == matching_session.userID).first()
		return user
	return None

def get_value_or_blank(request, value, type="POST"):
	#Returns either the value pulled from a request. Or defaults to nothing
	if (type == "POST"):
		return "" if request.form.get(value) is None else request.form.get(value)
	else:
		raise NotImplemented

class AlchemyEncoder(json.JSONEncoder):
	def default(self, obj):
	    if isinstance(obj.__class__, DeclarativeMeta):
	        # an SQLAlchemy class
	        fields = {}
	        for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
	            data = obj.__getattribute__(field)
	            try:
	                json.dumps(data) # this will fail on non-encodable values, like other classes
	                fields[field] = data
	            except TypeError:
	                fields[field] = None
	        # a json-encodable dict
	        return fields

	    return json.JSONEncoder.default(self, obj)

class PswdSafeAlchemyEncoder(json.JSONEncoder):
	def default(self, obj):
	    if isinstance(obj.__class__, DeclarativeMeta):
	        # an SQLAlchemy class
	        fields = {}
	        for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata' and (x != "password")]:
	            data = obj.__getattribute__(field)
	            try:
	                json.dumps(data) # this will fail on non-encodable values, like other classes
	                fields[field] = data
	            except TypeError:
	                fields[field] = None
	        # a json-encodable dict
	        return fields

	    return json.JSONEncoder.default(self, obj)


#######################
## Default responses ##
#######################

def was403(reason="Invalid permission"):
	return (reason, 403)

def was500(reason="Invalid data supplied"):
	return (reason, 500)

######################
## Core App Objects ##
######################
class User(DatabaseBase):
	__tablename__ = "Core_Users"

	id = Column(String(36), primary_key=True)
	username = Column(String)
	password = Column(String)
	display_name = Column(String)
	first_name = Column(String)
	last_name = Column(String)
	email = Column(String)
	salt = Column(String(36))

class Group(DatabaseBase):
	__tablename__ = "Core_Groups"

	id = Column(String(36), primary_key=True)
	name = Column(String)

class Group_User_Relation(DatabaseBase):
	__tablename__ = "Core_Groups_Users"

	relationID = Column(String(36), primary_key=True)
	userID = Column(String(36))
	groupID = Column(String(36))

class Session(DatabaseBase):
	__tablename__ = "Core_Sessions"

	id = Column(String(36), primary_key=True)
	userID = Column(String(36))
	addressIssued = Column(String)

class Core_Permission(DatabaseBase):
	__tablename__ = "Core_Permissions"

	id = Column(String(36), primary_key=True)
	name = Column(String(50))
	description = Column(String(300))
	machine_name = Column(String(50)) # Ex: users.create, users.delete, notes.create, notes.delete

################################
## Credential Related Objects ##
################################

#Going to need to split this up for security
class Credential(DatabaseBase):
	__tablename__ = "Credentials_Credentials"

	id = Column(String(36), primary_key=True)
	username = Column(String)
	password = Column(String)
	target = Column(String)
	notes = Column(String)
	displayName = Column(String)
	createdByID = Column(String(36), ForeignKey("Core_Users.id")) #UserID

class CredentialPermission(DatabaseBase):
	__tablename__ = "Credentials_User_Permissions"

	id = Column(String(36), primary_key=True)
	credentialID = Column(String(36), ForeignKey("Credentials_Credentials.id")) #Refers to Credential.id
	userID = Column(String(36), ForeignKey("Core_Users.id")) #Refers to User.id

	credential = relationship("Credential")

##########################
## Note Related Objects ##
##########################
class Notebook(DatabaseBase):
	__tablename__ = "Notes_Notebooks"

	id = Column(String(36), primary_key=True)
	createdByID = Column(String(36))
	permissionID = Column(String(36))
	title = Column(String)
	desc = Column(String)
	time_created = Column(DateTime(timezone=True), server_default=func.now())
	time_updated = Column(DateTime(timezone=True), onupdate=func.now())
	#editing_user = Column(String())

class NotebookPage(DatabaseBase):
	__tablename__ = "Notes_Pages"

	id = Column(String(36), primary_key=True)
	notebook_id = Column(String(36))
	createdByID = Column(String(36))
	permissionID = Column(String(36))
	content = Column(String)
	title = Column(String(20))

class NoteCategory_Note_Relation(DatabaseBase):
	__tablename__ = "Notes_CategoryRelations"

	id = Column(String(36), primary_key=True)
	category_id = Column(String(36))
	note_id = Column(String(36))

class NoteAccess(DatabaseBase):
	__tablename__ = "Notes_Access"

	id = Column(String(36), primary_key=True)
	userID = Column(String(36))
	permissionID = Column(String(36))
	type = Column(String(20))


#######################
## Initialize Server ##
#######################
# Create DB strucutre if it doesn't exist
DatabaseBase.metadata.create_all(db_engine)
main_session.commit()

app.run(debug=True)
