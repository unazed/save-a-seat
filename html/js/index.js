let CTX = {
  LOGIN: "login"
}, ERRS = {
  ERROR: "red",
  SUCCESS: "green",
  INFO: "blue"
}, SERVER_STATUS = {
  ERROR: 0x01,
  OK: 0x00
};


function generic_ensure_websocket(fn, default_, ...args)
{
  return (window.socket === undefined || window.socket.readyState !== 1)? default_(): fn(...args);
}

function create_notification(type, message)
{
  return console.log(message);
}

function assert_context(a, b)
{
  if (a !== b)
  {
    create_notificatiion(ERRS.ERROR, "internal error, invalid context");
    return false;
  }
  return true;
}

(function(initial_ctx) {
  'use strict'
  var ctx = initial_ctx;
  let ws_ready = false;
  let ensure_websocket = (fn) => (...args) => generic_ensure_websocket(fn, () => {
    create_notification(ERRS.ERROR, "internal error, the websocket is not ready");
    return false;
  }, ...args);
  let callback_table = {}, $$ = {
    "validate_login": (ctx) => {
      if (!assert_context(ctx, CTX.LOGIN)) { return; }
      const email = $("#emailInput").val(),
            password = $("#passwordInput").val();
      var failed = false;
      $$['validate_input'](ctx, "#emailInput");
      $$['validate_input'](ctx, "#passwordInput");
      if (!email.length)
      {
        $$['invalidate_input'](ctx, "#emailInput");
        failed = true;
      }
      if (!password.length)
      {
        $$['invalidate_input'](ctx, "#passwordInput");
        failed = true;
      }
      return !failed;
    },
    "invalidate_input": (ctx, input_id) => {
      return $(input_id).addClass("is-invalid");
    },
    "validate_input": (ctx, input_id) => {
      return $(input_id).removeClass("is-invalid")
                        .addClass("is-valid");
    },
    "submit_login": ensure_websocket((ctx) => {
      if (!assert_context(ctx, CTX.LOGIN)) { return; }
      $$.post("login", {
        email: $("#emailInput").val(),
        password: $("#passwordInput").val()
        }, (data) => {
          console.log("login callback", data);
        });
    }),
    "post": ensure_websocket((action, message, callback) => {
      if (typeof callback === "function")
      {
        callback_table[action] = callback;
      }
      return window.socket.send(JSON.stringify({action: action, data: message}));
    }),
    "websocket_open": () => {
      return create_notification(ERRS.SUCCESS, "websocket connection established");
    },
    "websocket_message": (event) => {
      const data = JSON.parse(event.data);
      if (data.status === SERVER_STATUS.ERROR)
      {
        return create_notification(ERRS.ERROR, `server: ${data.error}`);
      } else if (data.status === SERVER_STATUS.OK)
      {
        return callback_table[event.data.action](...data.data);
      }
    }
  };
  $(window).on("load", () => {
    window.socket = new WebSocket(`wss://${window.location.hostname}:443/wss`);
    window.socket.addEventListener("open", $$['websocket_open']);
    window.socket.addEventListener("message", $$['websocket_message']);
  });
  $("#submitBtn").click(() => {
    const email = $("#emailInput").val(),
          password = $("#passwordInput").val();
    if (!$$['validate_login'](ctx)) { return; }
    if (!$$['submit_login'](ctx))
    {
      create_notification(ERRS.ERRRO, "failed to login");
    }
    return $("#submitBtn").prop("disabled", true);
  });
})(CTX.LOGIN)
