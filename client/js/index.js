const session_data = require('./session_data');
const urls = require("./urls");
const request = require('request');

module.exports = {
  initialize_index: init,
}
function init(){
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
      $("#username_for_welcome_back").text(response.body);
    },
  })
}
