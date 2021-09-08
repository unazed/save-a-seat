(($$, ctx, current_ctx) => {
  if (!$$.assert_context(current_ctx, $$.CTX['watchlist']))
    { return ctx; }
  $("#control-body").html(`
  <p>this is the watchlist container!</p>
    `);
  return current_ctx;
})
