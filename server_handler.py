import aiohttp
from html import escape
from email.utils import parseaddr
is_valid_email = lambda email: '@' in parseaddr(email)[1]
import asyncio
import time
import hashlib
import inspect
import ipaddress
import uuid
import os
import pprint
import threading
import json

import utils.server_constants as server_constants
import libs.websocket_interface
import libs.scraper
import libs.paypal
import libs.course_watcher

import tinydb

from utils.server_constants import SERVER_EVENTS
from utils.utils import *
from libs.https_server import HttpsServer
from libs.websocket_interface import WebsocketPacket, CompressorSession
from ipc.thread_worker import ThreadWorker, Job
from ipc.proc_worker import ProcessWorker


class WebsocketClient:
    def __init__(self, headers, extensions, server, trans, addr, idx):
        libs.websocket_interface.EXTENSIONS.update(extensions)
        self.client_idx = idx
        self.trans = trans
        self.addr = addr
        self.server = server
        self.headers = headers

        comp = None
        self.comp = None
        if (params := extensions.get("permessage-deflate")) is not None:
            if (wbits := params.get("server_max_window_bits")) is None:
                self.comp = CompressorSession()
            else:
                self.comp = CompressorSession(int(wbits))
            print("creating compression object, wbits =", wbits)
        self.packet_ctor = WebsocketPacket(None, self.comp)

        self.__is_final = True
        self.__data_buffer = ""

        self.session = {}

    @chain
    def send(self, data, *args, pass_action=True, **kwargs):
        caller_name = inspect.currentframe().f_back.f_back.f_code.co_name
        # 2 `f_back`s from decorator
        if pass_action and caller_name.startswith("action_") \
                and isinstance(data, dict):
            data.update({"action": caller_name[7:]})
        with self.server.write_lock:
            self.trans.write(self.packet_ctor.construct_response(
                data, *args, **kwargs))

    def read_event(self, name, *, default=None):
        try:
            with open(f"html/events/{name}") as event:
                return event.read()
        except FileNotFoundError:
            if default is None:
                return
            with open(f"html/events/{default}") as default:
                return default.read()

    @authenticated
    def get_balance(self):
        records = self.server.payments_database.search(
                tinydb.Query().email == self.session['email']
                )
        balance = 0
        for order in records:
            if order['status'] in ("pending", "void"):
                continue
            balance += sum(float(unit['amount']['value']) \
                    for unit in order['purchase_units'])
        watchdog_deduction = len(self.get_watchdog())\
                        * server_constants.COURSE_PRICE
        return balance - watchdog_deduction

    @authenticated
    def get_watchdog(self, course=None):
        record = tinydb.Query()
        if course is None:
            return self.server.watchlist_database.search(
                    record.email == self.session['email'])
        subject, course, section = course
        return self.server.watchlist_database.search(
                (record.email == self.session['email'])
                & (record.subject_code == subject)
                & (record.course_code == course)
                & (record.section_code == section))

    @authenticated
    def action_load_courses(self):
        tid = self.server.thread_worker.place_job(
                Job("load_courses", self.client_idx))
        print(f"placed job {tid} for loading courses")
        return self.send({
            "status": False,
            "data": {"task_id": tid}
            })

    @authenticated
    def action_load_course(self, subject_code):
        tid = self.server.thread_worker.place_job(
                Job("load_course", self.client_idx, subject_code))
        print(f"placed job {tid} for loading course {subject_code}")
        return self.send({
            "status": False,
            "data": {"task_id": tid}
            })

    @authenticated
    def action_load_sections(self, subject_code, subcourse_code):
        tid = self.server.thread_worker.place_job(
                Job("load_sections", self.client_idx, (
                    subject_code, subcourse_code
                    )))
        print(f"placed job {tid} for loading sections from {subject_code}/"
              f"{subcourse_code}")
        return self.send({
            "status": False,
            "data": {"task_id": tid}
            })

    @authenticated
    def action_load_profile_info(self):
        return self.send({
            "status": False,
            "data": {
                "session_info": self.session,
                "balance": f"{self.get_balance():.2f}",
                "watchlist": self.get_watchdog()
                }
            })

    def action_login(self, email, password):
        password_hash = hashlib.sha512(password.encode()).hexdigest()
        user = tinydb.Query()
        if not (result := self.server.database.search(user.email == email)):
            return self.send({
                "status": True,
                "error": "no such email exists",
                "style": {
                    "#emailInput": ("+is-invalid", "-is-valid")
                    },
                "prop": {
                    "#submitBtn": {
                        "disabled": False
                        }
                    }
                })
        elif result[0]['password_hash'] != password_hash:
            return self.send({
                "status": True,
                "error": "incorrect password",
                "style": {
                    "#passwordInput": ("+is-invalid", "-is-valid")
                    },
                "prop": {
                    "#submitBtn": {
                        "disabled": False
                        }
                    }
                })
        session = result[0]
        if time.time() >= session['last_refreshed'] + session['refresh_in']:
            self.server.database.update(_ := {
                "last_refreshed": time.time(),
                "access_token": uuid.uuid1().hex
                })
            session.update(_)
        self.session = session
        return self.send({
            "status": False,
            "data": self.session
            }).send({
                "status": False,
                "action": "load",
                "data": self.read_event(SERVER_EVENTS['home']),
                "context": "HOME"
                }, pass_action=False)

    @authenticated
    def action_create_order(self, amount):
        if not amount.isdigit():
            return self.send({
                "status": True,
                "error": "invalid amount specified",
                "style": {
                    "#amount": ["+is-invalid", "-is-valid"]
                    }
                })
        amount = int(amount)
        if amount < 1:
            return self.send({
                "status": True,
                "error": "amount must be a positive integer",
                "style": {
                    "#amount": ["+is-invalid", "-is-valid"]
                    }
                })
        tid = self.server.thread_worker.place_job(
                Job("create_order", self.client_idx, amount))
        print(f"placed job {tid} to create order on ${amount}")
        return self.send({
            "status": False,
            "data": {"task_id": tid}
            })

    def create_order_callback(self, data):
        if data['type'] == "order":
            data = data['data']
            self.server.payments_database.insert({
                "email": self.session['email'],
                "order": data,
                "status": "pending"
                })

    @authenticated
    def action_load_control_item(self, name):
        if (path := server_constants.CONTROL_ITEM_MAP.get(name)) is None:
            return self.send({
                "status": True,
                "error": "control item unimplemented"
                })
        return self.send({
            "status": False,
            "action": "load",
            "data": self.read_event(path, default="unsupported.js"),
            "context": name
            }, pass_action=False)

    def action_login_with_token(self, access_token):
        user = tinydb.Query()
        if not (result := self.server.database.search(
                user.access_token == access_token)):
            return self.send({
                "status": True,
                "error": "token doesn't exist",
                })
        self.session = result[0]
        if time.time() >= self.session['last_refreshed'] + self.session['refresh_in']:
            self.session.clear()
            return self.send({
                "status": True,
                "error": "token expired"
                })
        return self.send({
            "status": False,
            "data": self.session
            }).send({
                "status": False,
                "action": "load",
                "data": self.read_event(SERVER_EVENTS['home']),
                "context": "HOME"
                }, pass_action=False)

    @authenticated
    def action_watch_course(self, subject_code, course_code, section_code):
        section_code = section_code.split()[-1]
        balance = self.get_balance()
        if balance <= 0:
            return self.send({
                "status": True,
                "error": "not enough balance",
                "style": {
                    "#watch-btn": ("-btn-outline-primary", "+btn-outline-danger")
                    }
                })
        elif (t := self.get_watchdog((subject_code, course_code,
                section_code))):
            return self.send({
                "status": True,
                "error": "watchdog already exists",
                "style": {
                    "#watch-btn": ("-btn-outline-primary", "+btn-outline-danger")
                    }
                })
        self.server.watchlist_database.insert({
            "email": self.session['email'],
            "subject_code": subject_code,
            "course_code": course_code,
            "section_code": section_code
            })
        tid = self.server.thread_worker.place_job(
                Job("watch_section", self.client_idx, (
                    subject_code, course_code, section_code
                    )))
        print(f"placed job {tid} for placing watchdog on {subject_code}, "
              f"{course_code}/{section_code}")
        return self.send({
            "status": False,
            "data": {"task_id": tid}
            })

    def action_register(self, email, password, password_confirm):
        if password != password_confirm:
            return self.send({
                "status": True,
                "error": "mismatching passwords",
                "style": {
                    "#passwordInput": ("+is-invalid", "-is-valid"),
                    "#passwordConfirmInput": ("+is-invalid", "-is-valid"),
                    }
                })
        elif not is_valid_email(email):
            return self.send({
                "status": True,
                "error": "invalid email",
                "style": {
                    "#emailInput": ("+is-invalid", "-is-valid")
                    }
                })
        user = tinydb.Query()
        if self.server.database.search(user.email == email):
            return self.send({
                "status": True,
                "error": "email already in use",
                "style": {
                    "#emailInput": ("+is-invalid", "-is-valid")
                    },
                "prop": {
                    "#submitBtn": {
                        "disabled": False
                        }
                    }
                })
        self.server.database.insert(session := {
            "email": email,
            "password_hash": hashlib.sha512(password.encode()).hexdigest(),
            "access_token": (access_token := uuid.uuid1().hex),
            "last_refreshed": time.time(),
            "refresh_in": server_constants.ACCESS_TOKEN_REFRESH_TIME
            })
        self.session = session
        return self.send({
            "status": False,
            "data": session
            })

    def __call__(self, prot, addr, data):
        if self.__data_buffer:
            data = self.__data_buffer
        data = self.packet_ctor.parse_packet(data)
        if data['extra']:
            self.__call__(prot, addr, data['extra'])
        self.__is_final = data['is_final']
        if not self.__is_final:
            self.__data_buffer += data['data']
            return
        elif self.__data_buffer:
            data = self.packet_ctor.parse_packet(self.__data_buffer + data['data'])
            self.__data_buffer = ""

        if data['opcode'] == 0x08:
            return self.trans.close()
        elif data['opcode'] == 0x0A:
            return
        elif data['opcode'] == 0x01:
            try:
                content = json.loads(data['data'])
            except json.JSONDecodeError as exc:
                self.send({
                    "error": "client sent invalid JSON"
                })
                print("received invalid JSON:", data['data'])
                return
            if (action := content.get("action")) is None:
                return self.send({
                    "status": True,
                    "error": "no `action` argument passed"
                    })
            elif (params := content.get("data")) is None:
                return self.send({
                    "status": True,
                    "error": "no `data` argument passed"
                    })
            elif (method := getattr(self, f"action_{action}", None)) is None:
                return self.send({
                    "status": True,
                    "error": "`action` doesn't exist" 
                    })

            try:
                method(**params)
            except TypeError as exc:
                print(exc, action, params)
                return self.send({
                    "status": True,
                    "error": "invalid arguments passed to `action` handler"
                    })

    def on_close(self, prot, addr, reason):
        ip = self.headers.get("cf-connecting-ip", addr[0])
        print(f"closed websocket with {ip!r}, reason={reason!r}")


_print = print


def print(*args, **kwargs):  # pylint: disable=redefined-builtin
    curframe = inspect.currentframe().f_back
    prev_fn = curframe.f_code.co_name
    line_no = curframe.f_lineno
    class_name = ""
    if (inst := curframe.f_locals.get("self")) is not None:
        class_name = f" [{inst.__class__.__name__}]"
        if hasattr(inst, 'authentication'):
            class_name += f" <{inst.authentication.get('username')}>"
    _print(f"[{time.strftime('%H:%M:%S')}] :{line_no} [ServerHandler]{class_name} [{prev_fn}]",
           *args, **kwargs)


async def main_loop(server):
    await server.handle_requests()


def preinit_whitelist(server, addr):
    ip = ipaddress.ip_address(addr[0])
    if not any(ip in net for net in server_constants.WHITELISTED_RANGES):
        print(f"prevented {addr[0]} from connecting due to whitelist")
        return server.trans.close()


if __name__ != "__main__":
    raise RuntimeError("this file cannot be imported, it must be run at the top level")

server = HttpsServer(
    root_directory="./",
    host="0.0.0.0", port=443,
    cert_chain=".ssl/cert.pem",
    priv_key=".ssl/key.pem",
    callbacks={
        "on_connection_made": preinit_whitelist
        },
    subdomain_map=server_constants.SUBDOMAIN_MAP
    )
server.write_lock = threading.Lock()


@server.route("GET", "/", subdomain="*")
def index_handler(metadata):
    return server.send_file(metadata, "html/index.html")

@server.route("GET", "/unsupported", get_params=["code"], subdomain="*")
def unsupported_handler(metadata, code=None):
    return server.send_file(metadata, "html/unsupported.html", format={
        "{error}": server_constants.ERROR_CODES.get(code,
            "The server hasn't specified a reason."
            )
        })

@server.route("websocket", "/wss", subdomain="*")
def websocket_handler(headers, idx, extensions, prot, addr, data):
    print("registering new websocket transport")
    if idx not in server.clients:
        server.clients[idx] = WebsocketClient(
            headers, extensions, server, prot.trans, addr, idx
        )
    prot.on_data_received = server.clients[idx]
    prot.on_connection_lost = server.clients[idx].on_close
    prot.on_data_received(prot.trans, addr, data)

@server.route("GET", "/*", subdomain="*")
def wildcard_handler(metadata):
    trans = metadata['transport']
    path = metadata['method']['path'][1:].split("/")
    if len(path) >= 2:
        folder, file = '/'.join(path[:-1]), path[-1]
        if folder not in server_constants.ALLOWED_FOLDERS:
            return trans.write(server.construct_response("Forbidden",
                error_body=f"<p>Folder {escape(folder)!r} isn't whitelisted</p>"
                ))
        headers = {}
        if isinstance((hdrs := server_constants.ALLOWED_FOLDERS[folder]), dict):
            headers = dict(filter(lambda i: not i[0].startswith("__"), hdrs.items()))
        files = os.listdir(folder)
        if file not in files:
            return trans.write(server.construct_response("Not Found",
                error_body=f"<p>File {escape(folder) + '/' + escape(file)!r} "
                           "doesn't exist</p>"
                ))
        return server.send_file(metadata, f"{'/'.join(path)}", headers={
            "content-type": server_constants.get_mimetype(file),
            **headers
        }, do_minify=False,
        read_kwargs=server_constants.ALLOWED_FOLDERS[folder].get(
            "__read_params", {}
        ) if server_constants.ALLOWED_FOLDERS[folder] is not None else {
            "mode": "r"
        })
    elif len(path) == 1:
        file = path[0]
        if (path := server_constants.ALLOWED_FILES.get(file)) is None:
            trans.write(server.construct_response("Forbidden",
                error_body=f"<p>File {escape(file)!r} isn't whitelisted</p>"
                ))
            return
        elif (redir := server_constants.ALLOWED_FILES[file].get("__redirect")) is not None:
            path = redir
        headers = {}
        if isinstance((hdrs := server_constants.ALLOWED_FILES[file]), dict):
            headers = dict(filter(lambda i: not i[0].startswith("__"), hdrs.items()))
        server.send_file(metadata, f"{path}", headers={
            "content-type": server_constants.get_mimetype(file),
            **headers
        }, do_minify=False,
        read_kwargs=server_constants.ALLOWED_FILES[file].get(
            "__read_params", {}
        ) if server_constants.ALLOWED_FILES[file] is not None else {
            "mode": "r"
        })
    trans.write(server.construct_response("Not Found",
        error_body=f"<p>File {escape(metadata['method']['path'])!r} "
                    "doesn't exist</p>"
        ))


if __name__ == "__main__":
    server.clients = {}
    server.database = tinydb.TinyDB("db/user.db")
    print(f"loaded user database ({len(server.database.all())} users)")
    server.payments_database = tinydb.TinyDB("db/payments.db")
    print("loaded payments database")
    server.watchlist_database = tinydb.TinyDB("db/watchlist.db")
    print(f"loaded watchlist database ({len(server.watchlist_database.all())} entries)")
    server.paypal = libs.paypal.Application(
            **read_creds(".auth/paypal.json"))
    print("initializing PayPal SDK")
    server.proc_worker = ProcessWorker(action_map={
        "load_courses": libs.scraper.load_courses,
        "load_course": libs.scraper.load_course,
        "load_sections": libs.scraper.load_sections,
        "create_order": server.paypal.create_order,
        "watch_section": libs.course_watcher.watch_section
        }, post_action_map={
        "create_order": lambda self, result: \
                (server.paypal.wait_for_order, (self, result,))
        }, callback_map={
        "create_order": "create_order_callback"
        })
    server.thread_worker = ThreadWorker(server, server.proc_worker)
    print("started process and thread workers")
    try:
        server.loop.run_until_complete(main_loop(server))
    except KeyboardInterrupt:
        for client in server.clients.values():
            client.trans.write(client.packet_ctor.construct_response(
                data=b"", opcode=0x8
                ))
        print("exiting gracefully...")
