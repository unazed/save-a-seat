def chain(fn):
    def inner(self, *args, **kwargs):
        fn(self, *args, **kwargs)
        return self
    return inner
