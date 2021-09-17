import aiohttp
import asyncio
import base64
import time
import json
import tinydb


class Order:
    def __init__(self, payment_obj, auth_token, session):
        self.payment_obj = payment_obj
        self._last_status = payment_obj
        self.auth_token = auth_token
        self.session = session
        self.authorized = False

    def get_link(self, name):
        return [link['href'] for link in self._last_status['links'] \
                if link['rel'] == name][0]

    def get_id(self):
        return self.payment_obj['id']

    def get(self, *args, **kwargs):
        headers = kwargs.get("headers", {})
        headers.update({
            'authorization': f"Basic {self.auth_token}",
            'content-type': "application/json"
            })
        return self.session.get(*args, **kwargs, headers=headers)

    def post(self, *args, **kwargs):
        headers = kwargs.get("headers", {})
        headers.update({
            'authorization': f"Basic {self.auth_token}",
            'content-type': "application/json"
            })
        return self.session.post(*args, **kwargs, headers=headers)

    async def get_status(self):
        async with self.get(self.get_link('self')) as status:
            self._last_status = await status.json()
            return self._last_status

    async def capture(self):
        async with self.post(self.get_link('capture')) as authorize:
            return await authorize.json()

    def __getstate__(self):
        return self._last_status
    __serialize__ = __getstate__

class Application:
    PAYPAL_OAUTH_API = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
    PAYPAL_ORDER_API = "https://api-m.sandbox.paypal.com/v2/checkout/orders"
    PAYPAL_ORDER_API_V1 = "https://api-m.sandbox.paypal.com/v1/checkout/orders/"
    def __init__(self, client_id, client_secret):
        self.auth_token = \
            base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        self.payments_database = tinydb.TinyDB("db/payments.db")

    def get(self, session, *args, **kwargs):
        headers = kwargs.get("headers", {})
        headers.update({
            'authorization': f"Basic {self.auth_token}",
            'content-type': "application/json"
            })
        return session.get(*args, **kwargs, headers=headers)

    def post(self, session, *args, **kwargs):
        headers = kwargs.get("headers", {})
        headers.update({
            'authorization': f"Basic {self.auth_token}",
            'content-type': "application/json"
            })
        return session.post(*args, **kwargs, headers=headers)

    def delete(self, session, *args, **kwargs):
        headers = kwargs.get("headers", {})
        headers.update({
            'authorization': f"Basic {self.auth_token}",
            'content-type': "application/json"
            })
        return session.delete(*args, **kwargs, headers=headers)

    async def create_order(self, server, amount, *, currency="CAD"):
        async with aiohttp.ClientSession() as session:
            async with self.post(session, self.PAYPAL_ORDER_API, json={
                    "intent": "CAPTURE",
                    "purchase_units": [
                        {
                            "amount": {
                                "currency_code": "CAD",
                                "value": round(amount, 2)
                                }
                            }
                        ]
                    }) as auth:
                return {
                    "data": Order(await auth.json(), self.auth_token, session)\
                        .__serialize__(),
                    "type": "order"
                    }

    def get_link(self, order, name):
        return [link['href'] for link in order['links'] \
                if link['rel'] == name][0]

    async def wait_for_order(self, server, order, expire_in=120):
        order = order['data']
        expires_at = time.time() + expire_in
        order_self = self.get_link(order, "self")
        async with aiohttp.ClientSession() as session:
            while True:
                if time.time() >= expires_at:
                    async with self.delete(session,
                            self.PAYPAL_ORDER_API_V1 + order['id']) as void:
                        assert void.status == 204
                        self.payments_database.update({
                            "status": "void"
                            }, tinydb.Query().order.id == order['id'])
                        return {
                            "data": "void",
                            "type": "status"
                            }
                async with self.get(session, order_self) as data:
                    order = await data.json()
                    if order['status'] == "APPROVED":
                        async with self.post(session,
                                self.get_link(order, "capture")) as authorize:
                            assert authorize.status == 201
                        self.payments_database.update({
                            **order,
                            "status": "approved"
                            }, tinydb.Query().order.id == order['id'])
                        return {
                            "data": "approved",
                            "type": "status"
                            }
                await asyncio.sleep(1)

