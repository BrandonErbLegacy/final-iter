const session_data = require('./session_data');
const urls = require("./urls");
const request = require('request');


module.exports = {
  init: init,
  set: {
    search: execute_search,
    row_left_click: set_left_click,
    row_right_click: set_right_click,
    limit_per_page: set_limit_per_page,
  },
  update: update_table,
}

var table_data_struct = {
  //Internal data store for local reference - limited to current page only
  data: {},
  //Jquery selector for table - for modifying specific table
  table: undefined,
  //Jquery selector for table header - for getting/hiding table columns
  table_header: undefined,
  //Jquery selector for table body - for manipulating table data
  table_body: undefined,
  //Jquery selector for table footer - for inserting pagination
  table_footer: undefined,
  //Jquery selector for search input - for binding to input
  table_search: undefined,

  //Functions - referenced on corresponding events by table
  events: {
    on_left_click: undefined,
    on_right_click: undefined,
  },

  //Urls - Used to retrieve data
  data_points: {
    normal_fetch: undefined,
    search_fetch: undefined,
    //The paginator will use the current Url to retrieve further results
    current: undefined,
    query: undefined,
  },

  limit_per_page: 5,
  total_items: undefined,
  current_page: undefined,
}

function init(table_id, data_fetch_url, search_url){
  //This table should display data given to it, but filter by headings only
  //Data not included in a th is stored in the js, but not actively displayed
  //It should be able to be retrieved by related table functions

  //Check to see if Jquery is loaded. It is required
  if ($ === undefined){
    console.err("JQuery has not been loaded. It is required");
    return;
  }

  table_data_struct.table = $("#"+table_id);
  table_data_struct.table_header = table_data_struct.table.find("#table-header");
  table_data_struct.table_body = table_data_struct.table.find("#table-body");
  table_data_struct.table_footer = table_data_struct.table.find("#table-footer");
  table_data_struct.table_search = table_data_struct.table.find("#table-search");

  table_data_struct.data_points.normal_fetch = data_fetch_url;
  table_data_struct.data_points.search_fetch = search_url;

  //Configure the textbox for searching
  table_data_struct.table_search.keypress(function(){
    setTimeout(function(){
      clearTimeout(400);
      query = table_data_struct.table_search.val();
      if (query == undefined || query == null || query.length == 0){
        fetch_paged_data(1);
      } else {
        fetch_search_data(1, query);
      }
      table_data_struct.data_points.query = query;
    }, 400);
  });
}

function fetch_search_data(page, query){
  table_data_struct.data_points.current  = table_data_struct.data_points.search_fetch;
  page = page - 1
  if (query == undefined){
    if (table_data_struct.data_points.query != undefined){
      query = table_data_struct.data_points.query;
    } else {
      console.log("No query was defined for searching");
    }
  }

  var options = {
    url: table_data_struct.data_points.search_fetch+"/"+query+"/"+page+"&"+table_data_struct.limit_per_page,
    method: "GET",
    fail: function(reason){
      alert("Failed to retrieve paged results");
      console.log(reason);
    },
    success: function(response){
      var parsed_response = JSON.parse(response.body);
      table_data_struct.total_items = parsed_response["count"];
      table_data_struct.current_page = page+1;
      table_data_struct.data = parsed_response["data"];
      render_rows(parsed_response["data"]);
      render_pagination(page+1);
    }
  }
  session_data.auth_request(options);
}
function fetch_paged_data(page){
  page = page - 1//This is done because the UI uses human friendly numbers
  //That way we don't start at 0 in the UI
  table_data_struct.data_points.current = table_data_struct.data_points.normal_fetch;
  var options = {
    url: table_data_struct.data_points.normal_fetch+"/"+page+"&"+table_data_struct.limit_per_page,
    method: "GET",
    fail: function(reason){
      alert("Failed to retrieve paged results");
      console.log(reason);
    },
    success: function(response){
      var parsed_response = JSON.parse(response.body);
      table_data_struct.total_items = parsed_response["count"];
      table_data_struct.current_page = page+1;
      table_data_struct.data = parsed_response["data"];
      render_rows(parsed_response["data"]);
      render_pagination(page+1);
    }
  }
  session_data.auth_request(options);
}
function render_rows(data_list){
  var html_to_insert = "";
  for (var row_id in data_list){
    //console.log(data_list[row_id]);
    html_to_insert = html_to_insert+ assemble_row(data_list[row_id], row_id);
  }
  table_data_struct.table_body.html(html_to_insert);
  bind_all_rows();
}
function render_pagination(current_page){
  var divisor = table_data_struct.total_items/table_data_struct.limit_per_page;
  divisor = divisor + 0.49; //This effectively always rounds to next highest digit
  var page_count = Math.round(divisor);
  var pagination_html = "<ul class='pagination'>";

  //On the only page
  if (current_page == page_count && (page_count < 2)){
    pagination_html = pagination_html + create_pagination_button('«', 'first', 'disabled');
    pagination_html = pagination_html + create_pagination_button('‹', 'prev', 'disabled');
    pagination_html = pagination_html + create_pagination_button('1', '1', 'disabled');
    pagination_html = pagination_html + create_pagination_button('›', 'next', 'disabled');
    pagination_html = pagination_html + create_pagination_button('»', 'last', 'disabled');
  } else {
    //Check if we can use the first button.
    if (current_page == 1){
      pagination_html = pagination_html + create_pagination_button('«', 'first', 'disabled');
      pagination_html = pagination_html + create_pagination_button('‹', 'prev', 'disabled');
    } else {
      pagination_html = pagination_html + create_pagination_button('«', 'first');
      pagination_html = pagination_html + create_pagination_button('‹', 'prev');
    }
    //More than 5 pages. So we have to worry about aligning and adding a page selector
    if (page_count > 5){
      if (current_page > 3){
        //Far enough we can omit pages on the left
        if (current_page+2 < page_count){
          //Enough pages we still have to omit pages on the right
          var i = current_page-2;
          while (i <= current_page+2){
            if (i == current_page){
              //console.log(pagination_html, create_pagination_button(i, i, 'active'));
              pagination_html = pagination_html + create_pagination_button(i, i, 'active');
            } else {
              pagination_html = pagination_html + create_pagination_button(i, i);
            }
            i++;
          }
        } else {
          //Far enough in we can't omit to the right. Only omit to the left.
          var i = page_count-4;
          while (i <= (page_count)){
            if (i == current_page){
              pagination_html = pagination_html + create_pagination_button(i, i, 'active');
            } else {
              pagination_html = pagination_html + create_pagination_button(i, i);
            }
            i++;
          }
        }
      } else {
        //We can't omit pages on the left. Omit pages on the right.
        var i = 1;
        while (i <= 5){
          if (i == current_page){
            //console.log(pagination_html, create_pagination_button(i, i, 'active'));
            pagination_html = pagination_html + create_pagination_button(i, i, 'active');
          } else {
            pagination_html = pagination_html + create_pagination_button(i, i);
          }
          i++;
        }
      }
    } else {
      //So few pages. Just display them.
      var i = 1;
      while (i <= page_count){
        if (i == current_page){
          //console.log(pagination_html, create_pagination_button(i, i, 'active'));
          pagination_html = pagination_html + create_pagination_button(i, i, 'active');
        } else {
          pagination_html = pagination_html + create_pagination_button(i, i);
        }
        i++;
      }
    }

    //Check if we can use the last button.
    if (current_page == page_count){
      pagination_html = pagination_html + create_pagination_button('›', 'next', 'disabled');
      pagination_html = pagination_html + create_pagination_button('»', 'last', 'disabled');
    } else {
      pagination_html = pagination_html + create_pagination_button('›', 'next');
      pagination_html = pagination_html + create_pagination_button('»', 'last');
    }
  }

  pagination_html = pagination_html + "</ul>";
  table_data_struct.table_footer.html(pagination_html);
  table_data_struct.table_footer.find(".page-link").each(function(){
    var obj = $(this);
    obj.click(function(){
      var target = obj.attr("data-target");
      var page_target = 0;
      if (target == "first"){
        page_target = 1;
      } else if (target == "last"){
        page_target = page_count;
      } else if (target == "next"){
        page_target = current_page+1;
      } else if (target == "prev"){
        page_target = current_page-1;
      } else if (target == "select"){
        return;
      } else {
        page_target = target;
      }
      if (table_data_struct.data_points.current == table_data_struct.data_points.normal_fetch){
        fetch_paged_data(page_target);
      } else {
        fetch_search_data(page_target);
      }
    });
  });
}
function create_pagination_button(text, data_target, state){
  //text - Non null
  //Data_target should be the data-target arg
  //State should be: undefined/null, active, or disabled
  var output = "";
  if (state != undefined){
    output = "<li class='page-item "+state+"'><a class='page-link' data-target='"+data_target+"'>"+text+"</a></li>"
  } else {
    output = "<li class='page-item'><a class='page-link' data-target='"+data_target+"'>"+text+"</a></li>"
  }
  return output;
}
function assemble_row(row_data, data_target){
  var output = "<tr data-target='"+data_target+"'>";
  table_data_struct.table_header.find("th").each(function(){
    var th_obj = $(this);
    var th_id = th_obj.prop("id")
    output = output+"<td>"+row_data[th_id]+"</td>";
  });
  output = output+"</tr>";
  return output;
}
function bind_all_rows(){
  table_data_struct.table_body.find("tr").each(function(){
    var obj = $(this);
    obj.click(function(){
      var data = table_data_struct.data[obj.attr("data-target")];
      if (table_data_struct.events.on_left_click != undefined){
        table_data_struct.events.on_left_click(data);
      }
    });
    obj.contextmenu(function(){
      var data = table_data_struct.data[obj.attr("data-target")];
      if (table_data_struct.events.on_right_click != undefined){
        table_data_struct.events.on_right_click(data);
      }
    });
  });
}

function set_left_click(func){
  table_data_struct.events.on_left_click = func;
}
function set_right_click(func){
  table_data_struct.events.on_right_click = func;
}
function set_limit_per_page(limit){
  table_data_struct.limit_per_page = limit;
}
function execute_search(query){
  fetch_search_data(1, query);
}

function update_table(){
  if (table_data_struct.data_points.current != undefined){
    if (table_data_struct.data_points.normal_fetch != undefined  && table_data_struct.data_points.current == table_data_struct.data_points.normal_fetch){
      fetch_paged_data(table_data_struct.current_page);
    } else if (table_data_struct.data_points.search_fetch != undefined  && table_data_struct.data_points.current == table_data_struct.data_points.search_fetch){
      fetch_search_data(table_data_struct.data_points.search_fetch);
    } else {
      console.log(table_data_struct.data_points);
    }
  } else if (table_data_struct.data_points.current == undefined && table_data_struct.data_points.normal_fetch != undefined){
    fetch_paged_data(1);
  }
}
