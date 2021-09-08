(($$, ctx, current_ctx) => {
  let navbar_toggled = false;
  if ( ctx !== $$.CTX.LOGIN && ctx !== $$.CTX.REGISTER )
  { return $$.assert_context(ctx, "login_or_register"); }
  $("#login-container").html(`
<div class="d-flex flex-column flex-grow-1">
  <div class="d-flex" id="top-bar">
    <nav class="ml-3 mr-3 navbar navbar-light" id="nav-bar">
      <button class="navbar-toggler collapsed" type="button">
        <span class="navbar-toggler-icon"></span>
      </button>
    </nav>
    <p>top bar</p>
  </div>
  <div class="d-flex flex-grow-1" id="control-container">
    <div class="pl-3 pr-3 flex-column" id="control-bar">
      <div>Watchlist</div>
      <div>Add credit</div>
      <div>Settings</div>
    </div>
    <div class="p-3 h-100 flex-grow-1 border" id="control-body">
      <h1>main container</h1>
    </div>
  </div>
  <div class="d-flex" id="bottom-bar">
    <small class='text-muted pt-1 mb-1 ml-2'>Copyright &copy; xchg 2021</small>
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor"
        class="bi bi-info-circle text-muted ml-auto mr-2 mt-1" viewBox="0 0 16 16">
      <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
      <path d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 6.588zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/>
    </svg>
  </div>
</div>
    `).prop("id", "home-container");
  $("#nav-bar").click(() => {
    console.log("clicked");
    if (!navbar_toggled)
    {
      $("#control-body").hide();
      $("#control-bar").show();
      navbar_toggled = true;
    } else
    {
      $("#control-body").show();
      $("#control-bar").hide();
      navbar_toggled = false;
    }
  });
})
