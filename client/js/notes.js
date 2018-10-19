const urls = require("./urls");
const session_data = require("./session_data");
const table_manager = require("./tablesv2");
const tab_manager = require('./tabmanager');
const {remote} = require('electron');
const {Menu, MenuItem} = remote
var Quill = require('quill');

var save_timer = undefined;

module.exports = {
  initialize_notes_editor: editor,
  initialize_notes_landing: landing,
}

function landing(){
  table_manager.init("all-notes-table", urls.paths.notes.notebooks.get_some, urls.paths.notes.notebooks.search);
  table_manager.update();

  table_manager.set.row_left_click(function(data){
    window.open("note_editor.html?id="+data["id"]);
    //view_cred(data["id"]);
  });
  table_manager.set.row_right_click(notebook_right_click);

  $("#modal-save").click(function(){
    var id = $("#modal-id").val();
    var title = $("#modal-title").val();
    var desc = $("#modal-desc").val();
    if (id != ""){
      notebook_update(id, title, desc);
      $("#modal-id").val("");
    } else {
      create_new_notebook(title, desc);
    }
  });

  var win = remote.getCurrentWindow();
  win.on('focus', () =>{
    table_manager.update();
  });
}

function create_new_notebook(title, desc){
  session_data.auth_request({
    url: urls.paths.notes.notebooks.save,
    method: "POST",
    data: {
      title: title,
      desc: desc,
    },
    fail: function(reason){
      alert("Failed to create a new notebook", reason);
    },
    success: function(response){
      var data = response.body;
      console.log(data);
      window.open("note_editor.html?id="+data);
      $("#create-note-modal").modal("toggle");
    },
  })
}

function notebook_update(id, title, desc){
  session_data.auth_request({
    url: urls.paths.notes.notebooks.save,
    method: "POST",
    data: {
      notebookID: id,
      title: title,
      desc: desc,
    },
    fail: function(reason){
      alert("Failed to update notebook", reason);
    },
    success: function(response){
      $("#create-note-modal").modal("toggle");
      table_manager.update();
    },
  })
}

function notebook_right_click(notebook){
  var id = notebook["id"];
  var context_menu = new Menu()
  context_menu.append(new MenuItem({label: 'Modify', click() {
    $("#create-note-modal").modal("toggle");
    $("#modal-id").val(id);
    $("#modal-title").val(notebook["title"]);
    $("#modal-desc").val(notebook["desc"]);
  }}));
  context_menu.append(new MenuItem({type: 'separator'}))
  context_menu.append(new MenuItem({label: 'Delete', click() {
    notebook_delete(id);
  }}));
  context_menu.popup({window: remote.getCurrentWindow()})
}

function notebook_delete(id){
  session_data.auth_request({
    url: urls.paths.notes.notebooks.delete,
    method: "POST",
    data: {
      notebookID: id
    },
    fail: function(reason){
      alert("Failed to delete", reason);
    },
    success: function(response){
      alert("Deleted notebook successfully!");
      table_manager.update();
    },
  })
}
function note_page_delete(pageID){
  session_data.auth_request({
    url: urls.paths.notes.pages.delete,
    method: "POST",
    data: {
      pageID: pageID
    },
    fail: function(reason){
      alert("Failed to delete", reason);
    },
    success: function(response){
      alert("Deleted page successfully!");
    },
  })
}

function editor(){
  console.log("Setting up");

  tab_manager.init("#tabs");
  var id = getUrlVars()["id"];

  $("#modal-save").click(function(){
    id = id.replace("#", "");

    page_id = $("#modal-id").val()

    if (page_id != ""){
      data = {
        notebookID: id,
        pages: JSON.stringify([
            {
              id: page_id,
              title: $("#modal-title").val(),
            },
        ]),
      }
    } else {
      data = {
        notebookID: id,
        pages: JSON.stringify([
            {
              title: $("#modal-title").val(),
              content: ""
            },
        ]),
      }
    }

    session_data.auth_request({
      url: urls.paths.notes.notebooks.save,
      method: "POST",
      data: data,
      fail: function(reason){
        alert("Failed to create a new page", reason);
      },
      success: function(response){
        $("#create-page-modal").modal("toggle");
        if ($("#modal-id").val() != ""){
          tab_manager.rename_current_tab($("#modal-title").val());
        } else {
          var data = JSON.parse(response.body);
          for (i in data){
            var cred = data[i];
            create_new_editor($("#modal-title").val(), "", true, cred);
          }
        }
        $("#modal-id").val("");
      },
    })
  });

  tab_manager.set_no_tabs_event(function(){
    $("body").prepend("<div class='empty-tab-list'>There are no pages left!<div class='empty-tab-list-action'><a href='#' id='new-tab-button'>Create one?</a></div></div>");
    $("#new-tab-button").click(function(){
      $("#create-page-modal").modal("toggle");
    });
  });

  tab_manager.set_on_tab_right_click(function(id){
    var page_id = $("#li"+id+" a").attr("data-target-note");
    var context_menu = new Menu()
    context_menu.append(new MenuItem({label: 'New page', click() {
      console.log("Trying new ");
      $("#create-page-modal").modal("toggle");
    }}));
    context_menu.append(new MenuItem({label: 'Rename page', click(){
      $("#modal-id").val(page_id);
      $("#create-page-modal").modal("toggle");
    }}));
    context_menu.append(new MenuItem({type: 'separator'}))
    context_menu.append(new MenuItem({label: 'Delete page', click() {
      note_page_delete(page_id);
      tab_manager.close_tab(id);
    }}));
    context_menu.popup({window: remote.getCurrentWindow()})
  });

  session_data.auth_request({
    url: urls.paths.notes.pages.get_by_notebook,
    method: "POST",
    data: {"notebookID":id},
    fail: function(reason){
      alert("Failed to load notes. Either there are none, or there's a server issue ", reason);
    },
    success: function(response){
      var creds = JSON.parse(response.body);
      for (var cred in creds){
        var info = creds[cred];
        console.log(info);
        if (cred == 0){
          create_new_editor(info.title, info.content, true, info);
        } else {
          create_new_editor(info.title, info.content, false, info);
        }
      }
    }
  });

  tab_manager.validate_tab_count();
}
function create_new_editor(title, contents, active, object){
  if (title != undefined){
    var id = tab_manager.create_new_tab(title, active);
  } else {
    var id = tab_manager.create_new_tab("New Tab", active);
  }
  $("#li"+id+" a").attr("data-target-note", object["id"]); // Insert the note page ID
  try {
    contents = JSON.parse(contents.trim());
  }
  catch (err){

  }
  $("#tab"+id).addClass("ql-wrap");
  $("#tab"+id).html("<div id='editor_"+id+"'></div>");
  var quill_editor = new Quill(('#editor_'+id), {
    //modules: { toolbar: '#toolbar' },
    modeuls: {
      toolbar: true,
    },
    theme: 'snow'
  });
  quill_editor.setContents(contents);

  quill_editor.on('text-change', function(delta, oldDelta, source){
    if (save_timer != undefined){
      clearTimeout(save_timer);
    }
    save_timer = setTimeout(function(){
      save_contents(quill_editor.getContents(), object);
    }, 1000);
  });

}
function save_contents(contents, originalObject){
  session_data.auth_request({
    url: urls.paths.notes.pages.update,
    method: "POST",
    data: {
      id: originalObject.id,
      content: JSON.stringify(contents),
      title: originalObject.title,
    },
    fail: function(reason){
      alert("Failed to save notes, ", reason);
    },
    success: function(response){
      console.log("Successful save");
    }
  });
}
function getUrlVars() {
    var vars = {};
    var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m,key,value) {
        vars[key] = value;
    });
    return vars;
}
