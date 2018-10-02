const fs = require('fs');
const request = require('request');
const AUTH_CODE_FILE = "AuthCode";

function write_auth_code(guid){
  fs.writeFileSync(AUTH_CODE_FILE, guid);
}
function read_auth_code(){
  if (fs.existsSync(AUTH_CODE_FILE)){
    return fs.readFileSync(AUTH_CODE_FILE, "utf8");
  } else {
    return undefined;
  }
}

var auth_code = {
  guid: undefined,
  get code(){
    this.guid = read_auth_code();
    return this.guid;
  },
  set code(guid){
    write_auth_code(guid);
    this.guid = guid;
  }
}

function make_auth_request({url, method, data, fail, success}){
  if (method != "GET" && method != "POST"){
    fail("An unsupported method was used");
  }

  var options = {
    url: url,
    method: method,
    headers: {
      "auth-id": auth_code.code,
    },
  }
  if (data != undefined){
    if (method == "POST"){
      options["form"] = data;
    } else if (method == "GET"){
      options["qs"] = data;
    }
  }

  request(options, function(err, response, body){
    if (!err && response.statusCode == 200) {
      success(response);
    } else {
      fail(err);
    }
  });
}

module.exports = {
  auth_code: auth_code,
  auth_request: make_auth_request,
}
