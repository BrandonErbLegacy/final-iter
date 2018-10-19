const urls = require("./urls");
const session_data = require("./session_data");
const table_manager = require("./tablesv2");
const {clipboard} = require('electron');

module.exports = {
  initialize_creds: init,
}

function init(){
  console.log("Setting up");
  var modal_id = $("#modal-id");
  var modal_display_name = $("#modal-display-name");
  var modal_username = $("#modal-username");
  var modal_password = $("#modal-password");
  var modal_target = $("#modal-target");

  var modal_copy_username_button = $("#modal-copy-username-button");
  var modal_copy_password_button = $("#modal-copy-password-button");
  $("#modal-save").click(function(){
    cred = {};
    cred.displayName = modal_display_name.val();
    cred.username = modal_username.val();
    cred.password = modal_password.val();
    cred.target = modal_target.val();
    cred_update(cred);
  });

  //Bind modal password to show on hover
  modal_password.hover(function(){
      modal_password.attr("type", "text");
    }, function(){
      modal_password.attr("type", "password");
  });

  modal_copy_username_button.click(function(){
    clipboard.writeText(modal_username.val());
    return false;
  });
  modal_copy_password_button.click(function(){
    clipboard.writeText(modal_password.val());
    return false;
  });

  table_manager.init("all-creds-table", urls.paths.credentials.get_some, urls.paths.credentials.search);
  table_manager.update();

  table_manager.set.row_left_click(function(data){
    view_cred(data["id"]);
  });
}


function view_cred(guid){
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
        cred_update(cred);
      });
    },
  });
}
function cred_update(cred){
  console.log("Triggered");
  if (cred.id != undefined){
    session_data.auth_request({
      url: urls.paths.credentials.update,
      method: "POST",
      data: cred,
      fail: function(reason) {
        alert("Failed to update credential, ", reason);
      },
      success: function(response){
        $("#modify-cred-modal").modal('hide');
        table_manager.update();
      },
    });
  } else {
    session_data.auth_request({
      url: urls.paths.credentials.create,
      method: "POST",
      data: cred,
      fail: function(reason) {
        alert("Failed to update credential, ", reason);
      },
      success: function(response){
        $("#modify-cred-modal").modal('hide');
        table_manager.update();
        reset_cred_modal();
      },
    });
  }
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
