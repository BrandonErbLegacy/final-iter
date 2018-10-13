// Modules to control application life and create native browser window
const {app, BrowserWindow} = require('electron')
const session_data = require('./js/session_data');
const urls = require("./js/urls");
const request = require('request');
// Keep a global reference of the window object, if you don't, the window will
// be closed automatically when the JavaScript object is garbage collected.
let mainWindow

function createWindow () {
  // Create the browser window.
  mainWindow = new BrowserWindow({width: 800, height: 600})

  //Load login.html if not already authenticated. Otherwise load login_success url
  if (session_data.auth_code.code != undefined) {
    var options = {
      url: urls.paths.users.session,
      method: "POST",
      headers: {
        "auth-id": session_data.auth_code.code,
      },
    }

    request(options, function(err, response, body){
      if (!err && response.statusCode == 200) {
        mainWindow.loadFile(urls.paths.redirects.login_success)
      } else {
        mainWindow.loadFile("login.html")
      }
    });
  } else {
    mainWindow.loadFile("login.html")
  }

  // Open the DevTools.
  // mainWindow.webContents.openDevTools()

  // Emitted when the window is closed.
  mainWindow.on('closed', function () {
    // Dereference the window object, usually you would store windows
    // in an array if your app supports multi windows, this is the time
    // when you should delete the corresponding element.
    mainWindow = null
  })
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', createWindow)

// Quit when all windows are closed.
app.on('window-all-closed', function () {
  // On OS X it is common for applications and their menu bar
  // to stay active until the user quits explicitly with Cmd + Q
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', function () {
  // On OS X it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (mainWindow === null) {
    createWindow()
  }
})

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and require them here.
