//Messy messy messy. Just a prototype
module.exports = {
  init: init,
  create_new_tab: create_new_tab,
  close_tab: close_tab,
  activate_tab: active_tab,
  set_on_tab_right_click: set_on_tab_right_click,
  set_no_tabs_event: set_no_tabs_event,
  validate_tab_count: validate_tab_count,
  rename_current_tab: rename_current_tab,
}

const tab_main_html = "<div class='bs-component' id='tab-manager-host'></div>";
const tab_head_html = "<ul class='nav nav-tabs' id='tab-manager-tab-heads'></ul>";
const tab_body_html = "<div class='tab-content' id='tab-manager-tab-bodys'></div>";
var tab_root = null;
var tab_head = null;
var tab_body = null;

var active_id = null;
var prev_active_id = null;
var right_click_action = null;
var no_tabs_event = null;

var tab_count = 0;

function check_dependencies(){
  if ($ == undefined){
    alert("Missing jQuery. It is required.");
  }
}

function init(selector, use_inital){
  check_dependencies();
  $(selector).html(tab_main_html);
  tab_root = $("#tab-manager-host");

  tab_root.html(tab_head_html);
  tab_root.append(tab_body_html);

  tab_head = $("#tab-manager-tab-heads");
  tab_body = $("#tab-manager-tab-bodys");

  if (use_inital == true){
    var initial_tab = create_new_tab("New Tab", true);
  }
}
function rename_current_tab(text){
  $('.nav-tabs a.active').text(text);
}

function set_on_tab_right_click(func){
  right_click_action = func;
}
function on_tab_right_click(tabID){
  if (right_click_action != null){
    right_click_action(tabID);
  }
}
function on_no_tabs_event(){
  if (set_no_tabs_event != null){
    no_tabs_event();
  }
}
function set_no_tabs_event(func){
  no_tabs_event = func;
}
function validate_tab_count(){
  if (tab_count == 0){
    on_no_tabs_event();
  }
}


function create_new_tab(title, activate){
  if (title == undefined){
    title = "New Tab";
  }
  var tab_id = guid();
  var tab_header = get_tab_head_html(title, tab_id);
  var tab_contents = get_tab_body_html(tab_id);

  tab_head.append(tab_header);
  tab_body.append(tab_contents);

  //Bind close button
  $("#li"+tab_id+" a").click(function(){
    tab_selected(tab_id);
  });
  $("#li"+tab_id+" a").contextmenu(function(){
    right_click_action(tab_id);
  });
  $("#close"+tab_id).click(function(){
    close_tab(tab_id);
  });

  if (activate == true){
    active_tab(tab_id);
  }

  tab_count = tab_count+1;

  return tab_id;
}
function tab_selected(tabID){
  if (active_id != null){
    prev_active_id = active_id;
  }
  active_id = tabID;
}
function close_tab(tab){
  var head = $("#li"+tab);
  head.remove();
  var body = $("#tab"+tab);
  body.remove();

  if (prev_active_id != null){
    active_tab(prev_active_id);
  }
  tab_count = tab_count -1;
  if (tab_count == 0){
    on_no_tabs_event();
  }
}
function active_tab(tabID){
  $('.nav-tabs a[href="#tab' + tabID + '"]').tab('show');
}

function get_tab_head_html(title, tab_id, active){
  var html = "<li class='nav-item' id='li"+tab_id+"'><a class='nav-link' data-toggle='tab' href='#tab";
  html = html + tab_id + "'>"+title+"<button class='closeTab' id ='close"+tab_id+"'>×</button></a></li>";
  return html;
}

function get_tab_body_html(tab_id, active){
  if (active == true){
    var html = "<div class='tab-pane fade show active' id='"+tab_id+"'></div>";
  } else {
    var html = "<div class='tab-pane fade' id='tab"+tab_id+"'></div>";
  }
  return html;
}

function guid() {
  function s4() {
    return Math.floor((1 + Math.random()) * 0x10000)
      .toString(16)
      .substring(1);
  }
  return s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4();
}
