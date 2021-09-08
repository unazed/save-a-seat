(($$, ctx, current_ctx) => {
  if (!$$.assert_context(current_ctx, $$.CTX['settings']))
    { return ctx; }
  $("#control-body").html(`
  <p>this is the settings page</p>
    `);
  return current_ctx;
})
