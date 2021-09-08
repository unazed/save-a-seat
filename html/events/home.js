(($$, ctx, current_ctx) => {
  if ( ctx !== $$.CTX.LOGIN && ctx !== $$.CTX.REGISTER )
  { return $$.assert_context(ctx, "login_or_register"); }
  $("#login-container").html(`
<div class="d-flex flex-column">
  <div class="d-flex" id="top-bar">
    <p>top bar</p>
  </div>
  <div class="d-flex" id="control-container">
    <div class="d-flex flex-column" id="control-bar">
      <p>entry 1</p>
      <p>entry 2</p>
      <p>entry 3</p>
    </div>
    <div class="container border" id="control-body">
      <h1>main container</h1>
    </div>
  </div>
  <div class="d-flex" id="bottom-bar">
    <p>bottom bar</p>
  </div>
</div>
    `).prop("id", "home-container");
})
