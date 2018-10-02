from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy import ForeignKey, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import load_only
from sqlalchemy.orm import relationship

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
		return "Invalid credentials", 403

	return ("%s : %s"%(hashed_password, matching_user.password))

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
		return "Invalid session.", 403

@app.route('/api/v1/users/session', methods=['POST'])
def users_session_validate():
	#TODO: Add session expiration. Also validation by IP to prevent session hijacking
	session_id = request.headers["auth-id"]
	session_obj = main_session.query(Session).filter(Session.id == session_id).first()
	if session_obj != None:
		return "OK", 200
	else:
		return "Invalid session.", 403

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
		return "Invalid session.", 403

@app.route('/api/v1/credentials/create', methods=['POST'])
def credentials_create():
	session_id = request.headers["auth-id"]
	user = get_user_by_session(session_id)
	if (user != None):
		cred = Credential()
		cred.id = new_uuid()
		cred.username = "" if request.form.get('username') is None else request.form.get('username')
		cred.password = "" if request.form.get('password') is None else request.form.get('password')
		cred.target = "" if request.form.get('target') is None else request.form.get('target')
		cred.notes = "" if request.form.get('notes') is None else request.form.get('notes')
		cred.displayName = "" if request.form.get('displayName') is None else request.form.get('displayName')
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
		return "Invalid session.", 403

@app.route('/api/v1/credentials/update', methods=['POST'])
def credentials_update():
	session_id = request.headers["auth-id"]
	user = get_user_by_session(session_id)
	if (user != None):
		credentialID = request.form.get('id')
		credPerm = main_session.query(CredentialPermission).filter(CredentialPermission.credentialID == credentialID).filter(CredentialPermission.userID == user.id).first()
		if (credPerm != None):
			cred = credPerm.credential
			cred.username = request.form.get('username')
			cred.password = request.form.get('password')
			cred.target = request.form.get('target')
			cred.notes = request.form.get('notes')
			cred.displayName = request.form.get('displayName')

			main_session.commit()
			return cred.id
		else:
			return "Invalid credential ID", 500
	else:
		return "Invalid session.", 403

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
			return "Invalid credential ID", 500
	else:
		return "Invalid session.", 403

@app.route('/api/v1/credentials/all/<int:page_num>&<int:limit>', methods=['GET'])
def credentials_get_page(page_num, limit):
	if (limit > 50):
		return "Invalid limit", 500
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
		return "Invalid session.", 403

@app.route('/api/v1/credentials/all/search/<string:query>/<int:page_num>&<int:limit>', methods=['GET'])
def credentials_get_query_page(query, page_num, limit):
	##Inefficient search algo
	##needs to update
	if (limit > 50):
		return "Invalid limit", 500
	session_id = request.headers["auth-id"]
	user = get_user_by_session(session_id)
	if (user != None):
		credentials_with_permission = main_session.query(CredentialPermission).filter(CredentialPermission.userID == user.id).order_by(CredentialPermission.id.desc())
		returnList = []
		for credPerm in credentials_with_permission:
			if (query in credPerm.credential.username):
				returnList.append(credPerm.credential)
				continue
			elif (query in credPerm.credential.password):
				returnList.append(credPerm.credential)
				continue
			elif (query in credPerm.credential.notes):
				returnList.append(credPerm.credential)
				continue
			elif (query in credPerm.credential.target):
				returnList.append(credPerm.credential)
				continue
			elif (query in credPerm.credential.displayName):
				returnList.append(credPerm.credential)
				continue
		sub_query = returnList[(page_num*limit):((page_num*limit)+limit)]
		returnItem = {"count":len(returnList), "data":sub_query}
		return json.dumps(returnItem, cls=PswdSafeAlchemyEncoder)
	else:
		return "Invalid session.", 403

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
	__tablename__ = "Note_Manager_Plugin_Notes"

	id = Column(String(36), primary_key=True)
	createdByID = Column(String(36))
	permissionID = Column(String(36))
	title = Column(String)

class NotebookPage(DatabaseBase):
	__tablename__ = "Note_Manager_Plugin_Notebook_Pages"

	id = Column(String(36), primary_key=True)
	notebook_id = Column(String(36))
	createdByID = Column(String(36))
	permissionID = Column(String(36))
	content = Column(String)
	title = Column(String(5))

class NoteCategory_Note_Relation(DatabaseBase):
	__tablename__ = "Note_Manager_Plugin_Note_Category_relations"

	id = Column(String(36), primary_key=True)
	category_id = Column(String(36))
	note_id = Column(String(36))

class NoteAccess(DatabaseBase):
	__tablename__ = "Note_Manager_Plugin_Note_Access"

	id = Column(String(36), primary_key=True)
	userID = Column(String(36))
	permissionID = Column(String(36))


#######################
## Initialize Server ##
#######################
# Create DB strucutre if it doesn't exist
DatabaseBase.metadata.create_all(db_engine)
main_session.commit()

app.run(debug=True)
