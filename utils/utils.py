def chain(fn):
    def inner(self, *args, **kwargs):
        fn(self, *args, **kwargs)
        return self
    return inner

def authenticated(fn):
    def inner(self, *args, **kwargs):
        if not self.session:
            return self.send({
                "status": True,
                "error": "must be authenticated to perform this action"
                })
        return fn(self, *args, **kwargs)
    return inner
