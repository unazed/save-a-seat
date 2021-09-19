function display_watch_dialog($$, subject_code, course_code, section_code)
{
  const modal = $(`
<div class="modal fade" tabindex="-1" role="dialog">
  <div class="modal-dialog modal-dialog-centered" role="document">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">${section_code}</h5>
        <button type="button" class="close" data-dismiss="modal">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
      <div class="modal-body">
        <p>Would you like to create a watchdog for:
          <b>${subject_code}, ${course_code}/${section_code}</b>?</p>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Close</button>
        <button type="button" class="btn btn-outline-primary" id="watch-btn">Watch</button>
      </div>
    </div>
  </div>
</div>
    `).modal('toggle').on('shown.bs.modal', () => {
      $("button#watch-btn").click(() => {
        return $$.post("watch_course", {
          "access_token": window.sessionStorage.getItem("access_token"),
          "subject_code": subject_code,
          "course_code": course_code,
          "section_code": section_code
          }, (data) => {
            if (data.task_id)
            {
              modal.modal('toggle');
              return create_notification($$.ERRS.SUCCESS, "created watchdog successfully");
            }
          });
      });
    });
}

function load_sections($$, subject_code, subcourse_code)
{
  $$.post("load_sections", {
    "access_token": window.sessionStorage.getItem("access_token"),
    "subject_code": subject_code,
    "subcourse_code": subcourse_code
    }, (data) => {
      if (data.task_id)
      {
        $("#section-view").html(`
        <small>Loading sections from <i>${subject_code}/${subcourse_code}</i>...</small>
          `);
        return create_notification($$.ERRS.INFO, `created task ${data.task_id}`);
      }
      $("#section-view").html(`
      <div id="section-tree">
      </div>
        `);
      var tree = new Tree(document.getElementById("section-tree")),
        branches = [{
          name: "Sections",
          open: true,
          type: Tree.FOLDER,
          children: []
        }];
      for (const section of data)
      {
        if (section.status === " ")
          { continue; }
        branches[0].children.push({
          name: section.section,
          open: true,
          type: Tree.FOLDER,
          subject_code: subject_code,
          course_code: subcourse_code,
          section_code: section.section,
          children: [
            {name: `Status: ${section.status}`},
            {name: `Activity: ${section.activity}`},
            {name: `Term: ${section.term}`}
          ]
        });
      }
      tree.json(branches);
      $("#section-view").find("summary").click((e) => {
        const target = $(e.target).parent();
        const subject_code = target.attr("x-code"),
              course_code = target.attr("x-course-code"),
              section_code = target.attr("x-section-code");
        if (subject_code === undefined)
          { return; }
        return display_watch_dialog($$, subject_code, course_code, section_code);
      });
    });
}

function load_course($$, subject_code)
{
  $$.post("load_course", {
    "access_token": window.sessionStorage.getItem("access_token"),
    "subject_code": subject_code
    }, (data) => {
      if (data.task_id)
      {
        $("#course-view").html(`
        <small>Loading subject <i>${subject_code}</i>...</small>
          `);
        return create_notification($$.ERRS.INFO, `created task ${data.task_id}`);
      }
      $("#course-view").html(`
      <div id="subcourse-tree">
      </div>
        `)
      var tree = new Tree(document.getElementById("subcourse-tree")),
        branches = [{
          name: "Courses",
          open: true,
          type: Tree.FOLDER,
          children: []
        }];
      for (const subcourse of data)
      {
        branches[0].children.push({
          name: `${subcourse.code}: ${subcourse.title}`,
          subject_code: subcourse.code,
        });
      }
      tree.json(branches);
      $("#subcourse-tree").find("a").click((e) => {
        const subcourse_code = $(e.target).attr("x-code");
        if (subcourse_code === undefined)
          { return; }
        return load_sections($$, subject_code, subcourse_code);
      });
    });
}

function load_all_courses($$)
{
  $$.post("load_courses", {
    "access_token": window.sessionStorage.getItem("access_token")
    }, (data) => {
      if (data.task_id)
        { return create_notification($$.ERRS.INFO, `created task ${data.task_id}`); }
      $("#course-select").html(`
        <div id="course-tree">
        </div>
      `);
      var tree = new Tree(document.getElementById("course-tree")),
          branches = [{
            name: "Subjects",
            open: true,
            type: Tree.FOLDER,
            children: []
          }];
      for (const course of data)
      {
        branches[0].children.push({
          name: course.title,
          open: false,
          type: Tree.FOLDER,
          subject_code: course.code,
          children: [{
            name: `Subject code: ${course.code}`
          }, {
            name: `School/faculty: ${course.school}`
          }]
        });
      }
      tree.json(branches);
      $("#course-select").find("summary").click((e) => {
        const subject_code = $(e.target).parent().attr("x-code");
        if (subject_code === undefined)
          { return; }
        return load_course($$, subject_code);
      });
    });
}

(($$, ctx, current_ctx) => {
  if (!$$.assert_context(current_ctx, $$.CTX['watchlist']))
    { return ctx; }
  var local_ctx = "view-courses";
  $("#control-body").html(`
  <div class="d-flex" id="course-container">
    <div class="d-flex flex-grow-1 flex-column" id="course-select-container">
      <p class="lead ml-auto mr-auto mt-3 pl-2 pr-2 mb-2 x-inactive" style="text-align: center"
        "view-watchdogs-btn">View your watchdogs</p>
      <div class="border p-2" id="course-select">
        <small>Loading subjects...</small>
      </div>
    </div>
    <div class="d-flex flex-column flex-grow-1">
      <div class="d-flex flex-grow-1 flex-column" id="course-view-container">
        <p class="lead ml-auto mr-auto mt-3 pl-2 pr-2 mb-2 x-active" style="text-align: center"
          id="view-courses-btn">View all subjects</p>
        <div class="border p-2 flex-grow-1" id="course-view">
          <small>Click any subject to view its information</small>
        </div>
      </div>
      <div class="border d-flex flex-grow-1 flex-column mt-2 p-2" id="section-view">
        <small>Click any course to view its sections</small>
      </div>
    </div>
  </div>
    `);
  load_all_courses($$);
  $("#view-courses-btn").click(() => {
    if (local_ctx !== "view-courses")
    {
      local_ctx = "view-courses";
      return load_all_courses($$);
    }
  });
  $("#view-watchdogs-btn").click(() => {
    if (local_ctx !== "view-watchdogs")
    {
      local_ctx = "view-watchdogs";
      return load_watchdogs($$);
    }
  });
  return current_ctx;
})
