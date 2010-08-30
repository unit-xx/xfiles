class dictdict(dict):
    def __getitem__(self, key):
        if not key in self:
            self.setdefault(key, dict())
        return dict.__getitem__(self, key)

class command:
    def __init__(self):
        self.cmdname = ""
        self.args = []
        self.kwargs = {}

    def __str__(self):
        return "cmdname: %s, args: %s, kwargs: %s" % (
                self.cmdname,
                self.args,
                self.kwargs,
                )

    def pack(self):
        msg = pickle.dumps(self, -1)
        msglen = len(msg)
        return pack("!I", msglen) + msg

def recv_n(conn, n):
    left = n
    content = []
    while 1:
        if left <= 0:
            break
        buf = conn.recv(left)
        content.append(buf)
        left = left - len(buf)

    return "".join(content)
