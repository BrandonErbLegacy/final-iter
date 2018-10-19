const session_data = require('./session_data');
const urls = require("./urls");
const request = require('request');

module.exports = {
  initialize_index: init,
}
function init(){

  /*var hamburger = $(".hamburger");
  hamburger.click(function(){
    hamburger.toggleClass("is-active");
  });*/

  var logout_button = $("#logout-button");
  logout_button.click(function(){
    session_data.auth_request({
      url: urls.paths.users.logout,
      method: "POST",
      data: {

      },
      fail: function(reason){
        alert("Failed to destroy session");
      },
      success: function(response){
        document.location = urls.paths.redirects.logout_success;
      },
    })
  });

  session_data.auth_request({
    url: urls.paths.users.get_username,
    method: "GET",
    data: {

    },
    fail: function(reason){
      alert("Failed to retrieve username");
    },
    success: function(response){
      $("#username_settings_button").text(response.body);
    },
  });
}
