import aiohttp
import asyncio
import base64
import json


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


class Application:
    PAYPAL_OAUTH_API = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
    PAYPAL_ORDER_API = "https://api-m.sandbox.paypal.com/v2/checkout/orders"

    def __init__(self, client_id, client_secret, session):
        self.auth_token = \
            base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        self.session = session

    async def create_order(self, amount, *, currency="CAD"):
        async with self.session.post(self.PAYPAL_ORDER_API, headers={
                "accept": "application/json",
                "authorization": (t := f"Basic {self.auth_token}")
                }, json={
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
            return Order(await auth.json(), self.auth_token, self.session)

    async def close(self):
        await self.session.close()

