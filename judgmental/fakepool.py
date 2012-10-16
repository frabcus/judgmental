class Pool:
    def close(self):
        pass
    def join(self):
        pass
    def apply_async(self,fn,args=(),callback=None):
        r = apply(fn,args)
        if callback:
            callback(r)
