(($$, ctx, current_ctx) => {
  if ( ctx !== $$.CTX.LOGIN && ctx !== $$.CTX.REGISTER )
  { return $$.assert_context(ctx, "login_or_register"); }
  $("#login-container").html(/* TODO */).prop("id", "home-container");
})
