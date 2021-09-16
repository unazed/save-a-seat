(($$, ctx, current_ctx) => {
  $("#control-body").html(`
  <p>lol</p>
  <div id="paypal-container">
  </div>
    `);
      paypal.Buttons({
        style: {
          color: "white",
          layout: "horizontal",
          tagline: false
        },
        createOrder: function(data, actions) {
          return actions.order.create({
            purchase_units: [{
              amount: {
                value: '77.44'
              }
            }]
          });
        },
        onApprove: function(data, actions) {
          return actions.order.capture().then(function(orderData) {
                console.log('Capture result', orderData, JSON.stringify(orderData, null, 2));
                var transaction = orderData.purchase_units[0].payments.captures[0];
                alert('Transaction '+ transaction.status + ': ' + transaction.id + '\n\nSee console for all available details');
          });
        }
      }).render('#paypal-container');
})
