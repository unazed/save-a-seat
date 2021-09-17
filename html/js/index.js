let CTX = {
  LOGIN: "login",
  REGISTER: "register",
  HOME: "home",
  watchlist: "watchlist",
  settings: "settings",
  "add-credit": "add-credit"
  
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
  $("#notification-container").append($(`
  <div class="notification">
    <small>${message}</small>
  </div>
    `).css({"border-left": `3px solid ${type}`}).fadeOut(3000));
  return console.log(message);
}

function assert_context(a, b)
{
  if (a !== b)
  {
    create_notification(ERRS.ERROR, "internal error, invalid context: " +
                                    `is ${a}, should be ${b}`);
    return false;
  }
  return true;
}

function apply_style_table(style_table)
{
  for (const [object, styles] of Object.entries(style_table))
  {
    for (const style of styles)
    {
      if (style.startsWith("-"))
      { $(object).removeClass(style.substring(1)); }
      else if (style.startsWith("+"))
      { $(object).addClass(style.substring(1)); }
    }
  }
}

function apply_prop_table(prop_table)
{
  for (const [object, props] of Object.entries(prop_table))
  { $(object).prop(props); }
}

(function(initial_ctx) {
  'use strict'
  let ctx = initial_ctx,
      ws_ready = false,
      ensure_websocket = (fn) => (...args) => generic_ensure_websocket(fn, () => {
        create_notification(ERRS.ERROR, "internal error, the websocket is not ready");
        return false;
      }, ...args),
      callback_table = {}, $$ = {
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
    "validate_register": (ctx) => {
      if (!assert_context(ctx, CTX.REGISTER)) { return; }
      const email = $("#emailInput").val(),
            password = $("#passwordInput").val(),
            confirm = $("#passwordConfirmInput").val();

      var failed = false;
      $$['validate_input'](ctx, "#emailInput");
      $$['validate_input'](ctx, "#passwordInput");
      $$['validate_input'](ctx, "#passwordConfirmInput");

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

      if (!confirm.length)
      {
        $$['invalidate_input'](ctx, "#passwordConfirmInput");
        failed = true;
      }

      if (password.length && confirm.length && (password != confirm))
      {
        $$['invalidate_input'](ctx, "#passwordInput");
        $$['invalidate_input'](ctx, "#passwordConfirmInput");
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
          window.sessionStorage.setItem("access_token", data.access_token);
          window.sessionStorage.setItem("refresh_at",
            data.last_refreshed + data.refresh_in);
        });
    }),
    "load": (data) => {
      ctx = (window.execScript || window.eval)(data.data)(
        $$, ctx, CTX[data.context]);
    },
    "assert_context": assert_context,
    "CTX": CTX,
    "ERRS": ERRS,
    "display_info_modal": (ctx) => {
      if (!assert_context(ctx, CTX.HOME)) { return; }
      $(`
<div class="modal fade" tabindex="-1" role="dialog">
  <div class="modal-dialog modal-dialog-centered" role="document">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Information</h5>
        <button type="button" class="close" data-dismiss="modal" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
      <div class="modal-body">
        <p>Monitor and receive notifications as soon as your university course
           becomes available. Quick, easy to use, and reliable.</p>
        <small class='text-muted'>Contact: xchngd@protonmail.com</small>
      </div>
    </div>
  </div>
</div>
        `).modal('show');
    },
    "submit_register": ensure_websocket((ctx) => {
      if (!assert_context(ctx, CTX.REGISTER)) { return; }
      $$.post("register", {
        email: $("#emailInput").val(),
        password: $("#passwordInput").val(),
        password_confirm: $("#passwordConfirmInput").val()
        }, (data) => {
          const access_token = data.access_token;
          window.sessionStorage.setItem('access_token', access_token);
          return $$['login_with_token'](ctx);
         });
    }),
    "post": ensure_websocket((action, message, callback) => {
      if (typeof callback === "function")
      { callback_table[action] = callback; }
      return window.socket.send(JSON.stringify({action: action, data: message}));
    }),
    "login_with_token": (ctx) => {
      const access_token = window.sessionStorage.getItem("access_token");
      if (access_token === null)
      { return create_notification(ERRS.ERROR, "no access token exists"); }
      return $$.post("login_with_token", {
        "access_token": access_token
        }, (data) => {
          return window.sessionStorage.setItem(
            "refresh_at", data.last_refreshed + data.refresh_in
          );
        });
    },
    "websocket_open": () => {
      const access_token = window.sessionStorage.getItem("access_token");
      if (access_token !== null)
      { $$['login_with_token'](ctx); }
      return create_notification(ERRS.SUCCESS, "websocket connection established");
    },
    "websocket_message": (event) => {
      const data = JSON.parse(event.data);
      console.log(data);
      if (data.status == SERVER_STATUS.ERROR)
      {
        if (data.style !== undefined)
        { apply_style_table(data.style); }
        if (data.prop !== undefined)
        { apply_prop_table(data.prop); }
        return create_notification(ERRS.ERROR, data.error);
      } else if (data.status == SERVER_STATUS.OK)
      {
        if (callback_table[data.action] !== undefined)
        { return callback_table[data.action](data.data); }
        else if ($$[data.action] !== undefined)
        { return $$[data.action](data); }
      }
    }
  };

  $(window).on("load", () => {
    window.socket = new WebSocket(`wss://${window.location.hostname}:443/wss`);
    window.socket.addEventListener("open", $$['websocket_open']);
    window.socket.addEventListener("message", $$['websocket_message']);
  });

  $(document).keypress(function (e) {
    if(e.which == 13)
    {
      switch (ctx)
      {
        case CTX.LOGIN:
        case CTX.REGISTER:
          $('#submitBtn').click();
          break;
        default:
          break;
      }
    }
  });   

  $("#registerText").click(() => {
    switch ($("#submitBtn").attr("x-method"))
    {
      case "login":
        ctx = CTX.REGISTER;
        $("#registerText").html("or login...");
        $("#passwordConfirmInput").parent().removeClass("d-none");
        $("#submitBtn").attr("x-method", "register").html("Register");
        break;
      case "register":
        ctx = CTX.LOGIN;
        $("#registerText").html("or register...");
        $("#passwordConfirmInput").parent().addClass("d-none");
        $("#submitBtn").attr("x-method", "login").html("Login");
        break;
    }
  });
  
  $("#submitBtn").click(() => {
    switch ($("#submitBtn").attr("x-method"))
    {
      case "login":
        if (!$$['validate_login'](ctx))
        { return; }
        $$['submit_login'](ctx);
        break;
      case "register":
        if (!$$['validate_register'](ctx))
        { return; }
        $$['submit_register'](ctx);
        break;
    }
    return $("#submitBtn").prop("disabled", true);
  });
})(CTX.LOGIN)
