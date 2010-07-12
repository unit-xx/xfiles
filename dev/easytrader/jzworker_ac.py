import sys
import asynchat
import Queue
import logging

import jz

class jzworker_ac(asynchat.async_chat):

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
        self.state = self.IDLE
        self.overlap = False
        self.task = None
        self.header_left = ""
        self.payload = ""

        self.req = None
        self.resp = None

    def allow_overlap(value):
        self.overlap = value

    def wait_head(self):
        self.state = self.WAIT_HEAD
        self.set_terminator(5) # 4 digits plus "|"

    def wait_headleft(self, length):
        self.state = self.WAIT_HEADLEFT
        self.set_terminator(length)

    def wait_payload(self, length):
        self.state = self.WAIT_PAYLOAD
        self.set_terminator(length)

    def idle(self):
        self.state = self.IDLE
        self.req = None
        self.resp = None

    def collect_incoming_data(self, data):
        self.ibuffer.append(data)

    def found_terminator(self):
        if self.state == self.WAIT_HEAD:

            header_len = int("".join(self.ibuffer)[0:4])
            del self.ibuffer[:]
            self.wait_headleft(header_len-5)

        elif self.state == self.WAIT_HEADLEFT:

            header_left = "".join(self.ibuffer)
            self.header_left = header_left
            del self.ibuffer[:]
            i = header_left.find("|")
            payload_len = int(header_left[0:i])
            if payload_len > 0:
                self.wait_payload(payload_len)
            else:
                self.payload = ""
                self.handleresp()

        elif self.state == self.WAIT_PAYLOAD:

            self.payload = "".join(self.ibuffer)
            del self.ibuffer[:]
            self.handleresp()

    def handleresp(self):
        self.resp.updatefrom(self.header_left, self.payload)
        if self.resp.hasnext == "1":
            nextreq = jz.GetNextReq(self.session)
            self.push(nextreq.serialize())
            self.wait_head()
        else:
            t = self.task
            param = t[2]
            callback = t[3]
            ifstoretrade = t[4]
            if ifstoretrade:
                self.dbqueue.put( (self.req, self.resp) )
            callback(self.req, self.resp, param)
            self.idle()

    def writable(self):
        if self.overlap or self.state == self.IDLE:
            if self.tqueue.qsize():
                try:
                    t = self.tqueue.get_nowait()
                    self.tqueue.task_done()
                    self.task = t

                    req = t[0](self.session)
                    self.req = req
                    param = t[2]
                    self.resp = t[1](self.session)
                    for k in param:
                        req[k] = param[k]
                    self.push(req.serialize())
                    self.wait_head()
                except Queue.Empty:
                    pass

        return asynchat.async_chat.writable(self) 
