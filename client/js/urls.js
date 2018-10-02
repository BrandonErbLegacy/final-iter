const base = "http://127.0.0.1:5000/api/v1/";
module.exports = {
  paths: {
    base: base,
    users: {
      create: base+"users/create",
      authenticate: base+"users/authenticate",
      update:base+"users/update",
      session: base+"users/session",
    },
    credentials: {
      create: base+"credentials/create",
      update: base+"credentials/update",
      delete: base+"credentials/delete",
      get_all: base+"credentials/all",
      //get_mine: base+"credentials/created_by_me",
      get_one: base+"credentials/",
      get_some: base+"credentials/all",
      search: base+"credentials/all/search",
    },

    redirects: {
      login_success: "index.html"
    }
  }
}
