const session_data = require('./session_data');
const urls = require("./urls");
const request = require('request');

function init(){
  $("#login-button").click(do_login);
}

function do_login() {
  username_field = $("#username-field");
  password_field = $("#password-field");

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
        console.log("Assigned session code of: ", session_data.auth_code.code);
    } else {
      alert("Failed to log in :(", err);
    }
  })
}

module.exports = {
  initialize_login: init,
}
