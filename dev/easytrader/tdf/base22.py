# -*- coding: utf-8 -*-
import logging
import socket

from datetime import datetime
from struct import pack, unpack, calcsize

ID_TDFTELE_UNDEF = 0
ID_TDFTELE_LOGIN = 1
ID_TDFTELE_LOGINANSWER = 2
ID_TDFTELE_LOGOUT = 3
ID_TDFTELE_CLOSE = 4
ID_TDFTELE_COCDETABLE = 6
ID_TDFTELE_REQDATA = 7
ID_TDFTELE_MARKETCLOSE = 8
ID_TDFTELE_TRADINGHALT = 9
ID_TDFTELE_TRANSACTION = 1101
ID_TDFTELE_ORDERQUEUE = 1102
ID_TDFTELE_ORDER = 1103
ID_TDFTELE_ORDERQUEUE_FAST = 1104
ID_TDFTELE_MARKETDATA = 1012
ID_TDFTELE_MARKETDATA_FUTURES = 1016
ID_TDFTELE_INDEXDATA = 1113
ID_TDFTELE_MARKETOVERVIEW = 1115
ID_TDFTELE_ADDCODE = 2001
ID_TDFTELE_SUBSCRIPTION = 2002
ID_TDFTELE_PLAYSPEED = 2003
ID_TDFTELE_REQETFLIST = 2004
ID_TDFTELE_ETFLISTFILE = 1116

ID_HDFDATAFLAGS_RETRANSALTE = 0x00000001#数据从开始传送
ID_HDFDATAFLAGS_NOTRANSACTION = 0x00000100#不传送逐笔成交数据
ID_HDFDATAFLAGS_NOABQUEUE = 0x00000200#不传送委托队列数据
ID_HDFDATAFLAGS_NOINDEX = 0x00000400#不传送指数数据
ID_HDFDATAFLAGS_NOMARKETOVERVIEW = 0x00000800#不传送 Market OverView 数据
ID_HDFDATAFLAGS_NOORDER = 0x00001000#不传送逐笔委托数据(SZ-Level2)
ID_HDFDATAFLAGS_COMPRESSED = 0x00010000#启用数据压缩
ID_HDFDATAFLAGS_ABQUEUE_FAST = 0x00020000#以FAST方式提供委托队列数据


class itemobj:
    def __str__(self):
        return str(self.__dict__)

class session:
    MAGIC = 0x5340

    headerfmt = "=HHiii"
    headerlen = calcsize(headerfmt)

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger()
        self.sock = None

    def setup(self):
        try:
            c = socket.socket()
            c.connect((self.config["tdfserver"], self.config["tdfport"]))
            self.sock = c
        except socket.error:
            self.close()
            return False
        return True

    def close(self):
        if self.sock is not None:
            self.sock.close()
            self.sock = None

    def recv_n(self, n):
        left = n
        content = []
        while 1:
            if left <= 0:
                break
            buf = self.sock.recv(left)
            content.append(buf)
            left = left - len(buf)
        return "".join(content)

    def packheader(self, req):
        msglen = len(req.payload)
        time = 0
        sn = 0
        return pack(self.headerfmt, self.MAGIC, req.code, msglen, time, sn)

    def sendheader(self, req):
        h = self.packheader(self, req)
        self.sock.sendall(h)

    def unpackheader(self, h):
        return unpack(self.headerfmt, h)

    def recvheader(self):
        h = self.recv_n(self.headerlen)
        return h

class request(object):
    code = ID_TDFTELE_UNDEF
    paramfmt = ""
    paramlen = calcsize(paramfmt)
    paramlist = []

    def __init__(self, session):
        self.payload = ""
        self.session = session

    def serialize(self):
        self.payload = pack(self.paramfmt,
                *[self.__getattribute__(x) for x in self.paramlist])
        self.header = self.session.packheader(self)

    def send(self):
        self.serialize()
        m = self.header+self.payload
        self.session.sock.sendall(m)
        #NOTE: strange, send header and payload separately will lead
        # to bugs: login failed.
        #self.session.sock.sendall(self.header)
        #self.session.sock.sendall(self.payload)

class response:
    paramfmt = ""
    paramlen = calcsize(paramfmt)
    paramlist = []

    def __init__(self, session):
        self.session = session
        self.code = ID_TDFTELE_UNDEF
        self.header = None
        self.payload = None

    def recv(self):
        # should be called by subclass who knows the message type
        self.header = self.session.recvheader()
        (magic, code, msglen, time, sn) = self.session.unpackheader(self.header)
        self.code = code
        self.payload = self.session.recv_n(msglen)
        self.parse()

    def frommsg(self, header, payload):
        # when created by respfactory dynamically on recved header/payload.
        self.header = header
        (magic, code, msglen, time, sn) = self.session.unpackheader(self.header)
        self.code = code
        self.payload = payload
        #print "code:%d"%self.code, "payloadlen:%d"%len(self.payload)
        self.parse()

    def parse(self):
        tmp = unpack(self.paramfmt, self.payload[0:self.paramlen])
        for i, p in enumerate(self.paramlist):
            self.__dict__[p] = tmp[i]

class response2(response):
    # response which has 2-level of data structure
    itemfmt = ""
    itemlen = calcsize(itemfmt)
    itemlist = []

    def parse(self):
        response.parse(self)
        self.parseitems()

    def parseitems(self):
        #print self.itemfmt
        #print self.nitem
        #print self.itemlen
        #print len(self.payload)
        #print self.paramlen

        self.items = []
        m = self.payload[self.paramlen:]
        # len(m) should equals to self.nitem*self.itemlen
        assert len(m) == self.nitem*self.itemlen
        for i in range(0, self.nitem*self.itemlen, self.itemlen):
            tmp = unpack(self.itemfmt, m[i:i+self.itemlen])
            tmp2 = itemobj()
            for j, p in enumerate(self.itemlist):
                tmp2.__dict__[p] = tmp[j]
            self.items.append(tmp2)

class loginReq(request):
    code = ID_TDFTELE_LOGIN
    paramfmt = "".join(["=16s", "32s", "8s", "32s"])
    paramlen = calcsize(paramfmt)
    paramlist = ["user", "passwd", "id", "chksum"]

    def login(self, u, p):
        self.user = u
        self.passwd = p
        self.id = ""
        self.chksum = ""
        self.send()

class loginResp(response):
    paramfmt = "".join(["=64s", "i", "i", "128s", "32i"])
    paramlen = calcsize(paramfmt)
    paramlist = ["info", "ans", "nmkt", "mktflag", "date"]

    def getmkts(self):
        self.markets = []
        for i in range(self.nmkt):
            start = i*4
            mkt = self.mktflag[start:start+4].strip("\x00")
            self.markets.append(mkt)
        return self.markets

class codetblReq(request):
    code = ID_TDFTELE_COCDETABLE
    paramfmt = "".join(["=4s", "i"])
    paramlen = calcsize(paramfmt)
    paramlist = ["mkt", "date"]

    def getcodetbl(self, mkt, date=0):
        self.mkt = mkt
        self.date = date
        self.send()

class codetblResp(response2):
    paramfmt = "".join(["=iiii"])
    paramlen = calcsize(paramfmt)
    paramlist = ["mktcode", "date", "nitem", "flag"]

    itemfmt = "".join(["=i", "i", "8s", "16s"])
    itemlen = calcsize(itemfmt)
    itemlist = ["idnum", "type", "secucode", "secuname"]

    def parse(self):
        response2.parse(self)

        for i in self.items:
            i.secuname = i.secuname.strip("\x00")
            i.secucode = i.secucode.strip("\x00")

class getquoteReq(request):
    code = ID_TDFTELE_REQDATA
    paramfmt = "".join(["=4s", "i"])
    paramlen = calcsize(paramfmt)
    paramlist = ["mkt", "flag"]

    def getquote(self, mkt, flag=0):
        self.mkt = mkt
        self.flag = flag
        self.send()

class futurequoteResp(response2):
    paramfmt = "".join(["=i"])
    paramlen = calcsize(paramfmt)
    paramlist = ["nitem"]

    itemfmt = "".join(["=3i", "q", "6I", "3q", "4I", "2i", "20I"])
    itemlen = calcsize(itemfmt)
    itemlist = ["idnum", "time", "status", "preopenint", "preclose",
            "presettleprice", "open", "high", "low", "match", "volume",
            "turnover", "openint", "close", "settleprice", "highlimit",
            "lowlimit", "predelta", "delta",
            "ask1", "ask2", "ask3", "ask4", "ask5",
            "askvol1", "askvol2", "askvol3", "askvol4", "askvol5",
            "bid1", "bid2", "bid3", "bid4", "bid5",
            "bidvol1", "bidvol2", "bidvol3", "bidvol4", "bidvol5",
            ]

class indexquoteResp(response2):
    paramfmt = "".join(["=i"])
    paramlen = calcsize(paramfmt)
    paramlist = ["nitem"]

    itemfmt = "".join(["=6i", "2q", "i"])
    itemlen = calcsize(itemfmt)
    itemlist = ["idnum", "time", "open", "high", "low", "last",
            "totalvol", "turnover", "preclose"]

class respfactory:
    dispatchmap = {
            ID_TDFTELE_MARKETDATA_FUTURES:futurequoteResp,
            ID_TDFTELE_INDEXDATA:indexquoteResp,
            }

    def __init__(self, session):
        self.session = session

    def dispatch(self):
        header = self.session.recvheader()
        (magic, code, msglen, time, sn) = self.session.unpackheader(header)
        payload = self.session.recv_n(msglen)
        try:
            resp = self.dispatchmap[code](self.session)
        except KeyError:
            resp = response(self.session)
        resp.frommsg(header, payload)
        return resp

