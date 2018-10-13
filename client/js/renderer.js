/* Almost globally required */
var $ = require('jquery');
window.$ = $;
window.jQuery = $;
require('bootstrap');


var login = require("./login");
var index = require("./index");
var credentials = require("./credentials");
var notes = require("./notes");

module.exports = {
  inits: {
    login: login.initialize_login,
    index: index.initialize_index,
    credentials: credentials.initialize_creds,
    notes_landing: notes.initialize_notes_landing,
    notes_editor: notes.initialize_notes_editor,
  }
}
