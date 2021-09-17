(($$, ctx, current_ctx) => {
  $("#control-body").html(`
  <div class="d-flex flex-column m-auto" id="payment-container">
    <small class='disclaimer text-muted'>
      Amounts are paid in CAD. Courses cost $1/per. Any deposits are
      irrefundable. Cost is not refunded if you decide to remove a watchdog, or
      if it completes.
    </small>
    <div class="input-group mb-3">
      <div class="input-group-prepend">
        <span class="input-group-text">$</span>
      </div>
      <input type="text" class="form-control" id="amount">
      <div class="input-group-append">
        <span class="input-group-text">CAD</span>
      </div>
    </div>
    <button type="button" class="btn btn-outline-dark m-auto"
        style="width: 50%" id="payment-btn">
      Pay with PayPal
    </button>
    <small class='mt-2 disclaimer' id="status"
        style="text-align: center!important">
    </small>
  </div>
    `);
  $("#payment-btn").click(() => {
    $$.post("create_order", {
      "access_token": window.sessionStorage.getItem("access_token"),
      "amount": $("#amount").val(),
    }, (data) => {
      if (data.task_id)
      {
        $("#payment-btn").prop("disabled", true);
        return create_notification($$.ERRS.INFO, `created task ${data.task_id}`);
      } else if (data.type === "order")
      {
        window.open(data.data.links[1]['href'], "SaveASeatPurchase",
          "menubar=yes,location=yes,resizable=yes,scrollbars=yes,status=yes");
        return create_notification($$.ERRS.SUCCESS, "order created");
      } else if (data.type === "status")
      {
        switch (data.data)
        {
          case "void":
            $("#status").html(`Your order has expired, please try again.`)
                        .addClass("text-danger");
            break;
          case "approved":
            $("#status").html(`Your order has been approved. The specified
              amount has been accredited to your account`)
                        .addClass("text-success");
            break;
        }
        $$.post("load_profile_info", {
          "access_token": window.sessionStorage.getItem("access_token")
          });
      }
    });
  });
})
