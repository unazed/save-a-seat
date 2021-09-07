(($$, ctx, current_ctx) => {
  if ( ctx !== $$.CTX.LOGIN && ctx !== $$.CTX.REGISTER )
  { return $$.assert_context(ctx, "login_or_register"); }
  $("#login-container").html(`
<p>hello</p>
    `).prop("id", "home-container");
})
