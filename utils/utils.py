import json


def chain(fn):
    def inner(self, *args, **kwargs):
        fn(self, *args, **kwargs)
        return self
    return inner


def authenticated(fn):
    def inner(self, *args, access_token=None, **kwargs):
        if not self.session:
            return self.send({
                "status": True,
                "error": "must be authenticated to perform this action"
                })
        elif self.session['access_token'] != access_token and access_token is not None:
            return self.send({
                "status": True,
                "error": "session token and passed token do not match"
                })
        return fn(self, *args, **kwargs)
    return inner


def read_creds(path):
    with open(path) as cred:
        return json.load(cred)
