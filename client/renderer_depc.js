// This file is required by the index.html file and will
// be executed in the renderer process for that window.
// All of the Node.js APIs are available in this process.
var $ = require('jquery');
window.$ = $;
window.jQuery = $;
require('bootstrap');
require('select2');
var fs = require('fs');
var crypto = require('crypto');
const request = require('request');
const urls = require("./urls");
require( 'datatables.net-bs4' )( $ );

var table_man = require("./js/table");


const session_data = require('./js/session_data');

function do_login() {
  username_field = $("#username_field");
  password_field = $("#password_field");

  username = username_field.val();
  password = password_field.val();

  console.log("Attempting login");
  var options = {
    url: urls.paths.users.authenticate,
    method: "POST",
    headers: {

    },
    form: {
      "username":username,
      "password":password
    }
  }

  request(options, function(err, response, body){
    if (!err && response.statusCode == 200) {
        // Print out the response body
        session_data.auth_code.code = response.body;
        document.location = urls.paths.redirects.login_success;
    } else {
      alert("Failed to log in :(", err);
    }
  })
}

function initialize_login(){
  console.log("Creating login page");
  $("#login_button").click(do_login);

  //console.log(session_data.auth_code);
  session_data.auth_code.code = "new1";
  console.log(session_data.auth_code.code);
}

function initialize_index(){
  console.log(session_data.auth_code.code);
}

function initialize_create_cred(){
  $("#submit").click(submit_create_cred);
}
function initialize_view_multi_cred(){
  $("#modal-password").hover(function(){
    $("#modal-password").attr('type', "text");
  },
  function(){
    $("#modal-password").attr('type',"password");
  });

  session_data.auth_request({
    url: urls.paths.credentials.get_all,
    method: "GET",
    fail: function(reason) {
      alert("Failed to retrieve all credentials, ", reason);
    },
    success: function(response){
      var table = $("#table-body");
      var json = JSON.parse(response.body);
      var own = json["owned"];
      var by_user = json["by_user"];
      var all = own;
      for (var i in by_user){
        all.push(by_user[i]);
      }
      table_man.init("all-creds-table", "target_api", ["id"]);
      table_man.render(all);
      table_man.add_click_bind(function(obj, data){
        view_cred(data["id"], obj);
      });
    },
  });
}

function view_cred(guid, row){
  var modal_id = $("#modal-id");
  var modal_display_name = $("#modal-display-name");
  var modal_username = $("#modal-username");
  var modal_password = $("#modal-password");
  var modal_target = $("#modal-target");
  session_data.auth_request({
    url: urls.paths.credentials.get_one+guid,
    method: "GET",
    fail: function(reason) {
      alert("Failed to retrieve credential, ", reason);
    },
    success: function(response){
      var cred = JSON.parse(response.body);
      modal_id.val(cred.id);
      modal_display_name.val(cred.displayName);
      modal_username.val(cred.username);
      modal_password.val(cred.password);
      modal_target.val(cred.target);
      $("#modalLabel").text("Credential: "+cred.displayName);
      $("#modify-cred-modal").modal('show');

      $("#modal-save").click(function(){
        cred.displayName = modal_display_name.val();
        cred.username = modal_username.val();
        cred.password = modal_password.val();
        cred.target = modal_target.val();
        cred.id = modal_id.val();
        cred_update(cred, row);
      });
    },
  });
}
function cred_update(cred, row){
  session_data.auth_request({
    url: urls.paths.credentials.update,
    method: "POST",
    data: cred,
    fail: function(reason) {
      alert("Failed to update credential, ", reason);
    },
    success: function(response){
      $("#modify-cred-modal").modal('hide');
      var newD = table_man.rerender_single_row(cred);
      row.html(newD);
    },
  });
}
function reset_cred_modal(){
  var modal_id = $("#modal-id");
  var modal_display_name = $("#modal-display-name");
  var modal_username = $("#modal-username");
  var modal_password = $("#modal-password");
  var modal_target = $("#modal-target");

  modal_id.val("");
  modal_display_name.val("");
  modal_username.val("");
  modal_password.val("");
  modal_target.val("");
}

function submit_create_cred(){
  var username = $("#username_field").val();
  var password = $("#password_field").val();
  var target = $("#target_field").val();
  var displayName = $("#display_field").val();
  var notes = $("#notes_field").val();

  session_data.auth_request({
    url: urls.paths.credentials.create,
    method: "POST",
    data: {
      "username":username,
      "password":password,
      "target":target,
      "displayName":displayName,
      "notes":notes
    },
    fail: function(reason) {
      alert("Failed to create a new credential, ", reason);
    },
    success: function(response){
      console.log("Success");
    },
  });
}

module.exports = {
  inits: {
    login: initialize_login,
    index: initialize_index,
    credentials: {
      create: initialize_create_cred,
      view: initialize_view_multi_cred,
    }
  }
}
