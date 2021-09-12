(($$, ctx, current_ctx) => {
  if (!$$.assert_context(current_ctx, $$.CTX['watchlist']))
    { return ctx; }
  $("#control-body").html(`
  <div class="d-flex" id="course-container">
    <div class="d-flex flex-grow-1 flex-column" id="course-select-container">
      <p class="lead ml-auto mr-auto mt-3 pl-2 pr-2 mb-2 x-active" style="text-align: center">View your watchdogs</p>
      <div class="border p-2" id="course-select">
        <small>Loading courses</small>
      </div>
    </div>
    <div class="d-flex flex-grow-1 flex-column" id="course-view-container">
      <p class="lead ml-auto mr-auto mt-3 pl-2 pr-2 mb-2 x-inactive" style="text-align: center">View all courses</p>
      <div class="border p-2" id="course-view">
        <small>Click any course to view its information</small>
      </div>
    </div>
  </div>
    `);

  $$.post("load_courses", {
    "access_token": window.sessionStorage.getItem("access_token")
    }, (data) => {
      console.log(data);
    });
  return current_ctx;
})
