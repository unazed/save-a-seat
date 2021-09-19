from ipaddress import ip_network
from functools import partial
import math


def get_mimetype(name):
    return MIMETYPES.get(name.split(".")[-1], "text/plain")


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

SERVER_EVENTS = {
        "home": "home.js"
        }

CONTROL_ITEM_MAP = {
        "watchlist": "watchlist.js",
        "add-credit": "add-credit.js",
        "settings": "settings.js"
        }

ACCESS_TOKEN_REFRESH_TIME = 60 * 60 * 24  # 1 day
COURSE_PRICE = 1
