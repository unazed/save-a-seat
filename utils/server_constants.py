from ipaddress import ip_network
from functools import partial
import math


def get_mimetype(name):
    return MIMETYPES.get(name.split(".")[-1], "text/plain")


def when_authenticated(name, must_have_auth=True):
    def inner(auth):
        if not auth and not must_have_auth:
            return f"html/events/{name}"
        elif not auth:
            return SUPPORTED_WS_EVENTS['forbidden']
        return f"html/events/auth/{name}"
    return inner


ERROR_CODES = {
    "400": "Websockets are unsupported on your platform "
         "consider upgrading your browser. Without websockets "
         "we would not be able to serve this webpage to you."
}

MIMETYPES = {
    "js": "text/javascript",
    "css": "text/css",
    "html": "text/html",
    "ico": "image/x-icon",
    "svg": "image/svg+xml"
}

WHITELISTED_RANGES = [*map(ip_network, [
    "0.0.0.0/0"
    ])]

SUBDOMAIN_MAP = {
    "www": "html/",
    "admin": "admin/"
    }

ALLOWED_FOLDERS = {
    "html/css": {
        "Cache-Control": "nostore"
        },
    "html/js": {
        "Cache-Control": "nostore"
        },
    "html/img": {
        "Cache-Control": "nostore",
        "__read_params": {
            "mode": "rb"
            }
        },
    "admin/js": {
        "Cache-Control": "nostore"
        },
    "admin/css": {
        "Cache-Control": "nostore"
        }
    }

ALLOWED_FILES = {
    "favicon.ico": {
        "__redirect": "html/img/favicon.ico",
        "__read_params": {
            "mode": "rb"
            }
        }
    }
