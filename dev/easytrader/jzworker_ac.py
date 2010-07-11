import sys
import async_chat
import Queue

import jz

class jzworker(asynchat.async_chat):

    IDLE = 0
    WAIT_HEAD = 1
    WAIT_HEADLEFT = 2
    WAIT_PAYLOAD = 3

    def __init__(self, jzsession, tqueue, dbqueue):
        asynchat.async_chat.__init__(self,
                sock=jzsession.sockconn)
        self.session = jzsession
        self.tqueue = tqueue
        self.dbqueue = dbqueue
        self.logger = logging.getLogger()
        self.ibuffer = []
        self.state = jzworker.IDLE
        self.overlap = False

    def allow_overlap(value):
        self.overlap = value

    def wait_head(self):
        self.state = jzworker.WAIT_HEAD
        self.set_terminator(4)

    def wait_headleft(self, length):
        self.state = jzworker.WAIT_HEADLEFT
        self.set_terminator(length)

    def wait_payload(self, length):
        self.state = jzworker.WAIT_PAYLOAD
        self.set_terminator(length)

    def idle(self):
        self.state = jzworker.IDLE

    def collect_incoming_data(self, data):
        self.ibuffer.append(data)

    def found_terminator(self):
        if self.state == jzworker.WAIT_HEAD:
            self.wait_headleft()
        elif self.state == jzworker.WAIT_HEADLEFT:
            self.wait_payload()
        elif self.state == jzworker.WAIT_PAYLOAD:
            self.idle()

    def writable(self):
        if self.overlap or self.state == jzworker.IDLE:
            if self.tqueue.qsize():
                try:
                    t = self.tqueue.get_nowait()
                    self.tqueue.task_done()

                    req = t[0](self.session)
                    param = t[2]
                    for k in param:
                        req[k] = param[k]
                    self.push(req.serialize())
                    self.wait_head()
                except Queue.Empty:
                    pass

        return asynchat.async_chat.writable(self) 
