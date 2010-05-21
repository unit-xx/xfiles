# -*- coding: utf-8 -*-

import socket
import datetime
import sqlite3 as db
import logging

CFFEXCODE = "G"

class session:
    def __init__(self, sessioncfg):
        self.sessioncfg = sessioncfg
        self.conn = None
        self.tradedbconn = None
        self.data = {}
        self.logger = logging.getLogger()

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def setup(self):
        try:
            c = socket.socket()
            c.settimeout(10)
            c.connect((self.sessioncfg["jsdserver"], self.sessioncfg["jsdport"]))
            self.conn = c

            self.tradedbconn = db.connect(self.sessioncfg["tradedbfn"])
        except socket.error:
            return False

        self["jsdaccount"] = self.sessioncfg["jsdaccount"]
        self["jsdpasswd"] = self.sessioncfg["jsdpasswd"]
        self["branchcode"] = self.sessioncfg["branchcode"]
        self["ordermethod"] = self.sessioncfg["ordermethod"]

        loginreq = LoginReq(self)
        loginreq.send()
        loginresp = LoginResp(self)
        loginresp.recv()
        if loginresp.anwser != "Y":
            self.logger.warning("Login failed")
            return False

        getcnreq = GetClientNumReq(self)
        getcnreq["exchcode"] = CFFEXCODE
        getcnreq.send()
        getcnresp = GetClientNumResp(self)
        getcnresp.recv()
        if getcnresp.anwser != "Y" or len(getcnresp.records) == 0:
            self.logger.warning("Login failed")
            return False

        self["clientnum"] = getcnresp.records[0][2]
        self["seat"] = getcnresp.records[0][4]

        self.logger.info("Login ok")
        return True

    def storetrade(self, req, resp):
        t = datetime.now()
        self.tradedbconn.execute('insert into rawtradeinfo values (?, ?, ?, ?)',
                (str(t),
                    req.payload.decode("GBK"),
                    resp.payload.decode("GBK"),
                    "%s:%s" % (resp.retcode, resp.retinfo)
                    ))
        self.tradedbconn.commit()

    def close(self):
        self.tradedbconn.commit()
        self.tradedbconn.close()
        self.conn.close()

class request:
    """
    a sample:
R|||6011|||9201|123|
    """
    code = ""
    paramlist = [] # fields after user and password

    def __init__(self, session):
        self.session = session
        # attribute values
        self.params = {}

    def __getitem__(self, key):
        try:
            return self.params[key]
        # in case a param is not set, we assume it is empty
        except KeyError: 
            return " "

    def __setitem__(self, key, value):
        self.params[key] = value

    def updateparams(self, params):
        self.params.update(params)

    def serialize(self):
        header = self.genheader()
        payload = self.genpayload()
        self.payload = payload
        return "".join( (header, payload) )

    def genheader(self):
        return "R|||"

    def genpayload(self):
        params = [self[k] for k in self.paramlist]
        tmp = [self.code, self.session["branchcode"],
                self.session["ordermethod"],
                self.session["jsdaccount"],
                self.session["jsdpasswd"]]
        tmp.extend(params)
        return "|".join(tmp)

    def send(self):
        data = self.serialize()
        self.session.conn.sendall(data)

class response:
    """
    a sample:
A|||Y|中投证券|0.03|0.00|0|20100513|172.30.4.165|20100513|14:57:51|7|1|0|0||1000000000|6.6.5|800|Kingstar|20100513|2771009183|黑龙江天琪期货|4/512|0

    note: there may or may not be a '|' at the end of response. the above
    sample is the response of login, and the following response of 6012
    has '|' at the end

A|||Y|中投证券|97272165.62|0.00|0.00|347328.00|2324049.60|0.00|0.00|94304028.02|
96975405.62|0.0275|0|0.00|-296760.00|0.00|0.00|0.00|0.00|0.00|0.00|2671377.60|23
63227.20|0.00|0.00|1|
    
    """
    okfieldn = 0
    failfieldn = 3 # N, retcode, retinfo
    hasmore = 0

    def __init__(self, session):
        self.session = session
        self.records = []

    def recv_single(self):
        # jsd does not include header/payload length in protocol, so
        # we just try to receive a long buffer, and with some assertions
        # to make things right.
        data = self.session.conn.recv(8192)
        assert data[0] == "A"

        data = data.decode("GBK")
        record = data.split("|")[3:]
        if record[-1] == "":
            # the case when '|' at the end
            del record[-1]
        if record[0] == "Y":
            assert len(record) >= self.okfieldn, "less record fields: %d vs. %d" % (len(record), self.okfieldn)
        elif record[0] == "N":
            assert len(record) >= self.failfieldn
            self.failcode = record[1]
            self.failinfo = record[2]
        else:
            assert False, "Not valid response"
        self.anwser = record[0]
        self.records = []
        self.records.append(record)
        self.nrec = 1

    def recv_many(self):
        # the case then multiple recv is needed, and the first package denote the number of succesive packages
        data = self.session.conn.recv(8192)
        data = data.decode("GBK")
        assert data[0] == "A"
        record = data.split("|")[3:]
        if record[-1] == "":
            # the case when '|' at the end
            del record[-1]

        self.anwser = record[0]
        if record[0] == "Y":
            nrec = int(record[1])
            self.nrec = nrec
            # read next packages
            records = []
            getnextreq = GetNextReq(self.session)
            for i in range(nrec):
                try:
                    getnextreq.send()
                    data = self.session.conn.recv(8192)
                    data = data.decode("GBK")
                    record = data.split("|")[3:]
                    if record[-1] == "":
                        # the case when '|' at the end
                        del record[-1]
                    assert len(record) >= self.okfieldn, "less record fields: %d vs. %d" % (len(record), self.okfieldn)
                    records.append(record)
                except socket.timeout:
                    pass
        elif record[0] == "N":
            assert len(record) >= self.failfieldn
            self.failcode = record[1]
            self.failinfo = record[2]
        else:
            assert False, "Not valid response"
        self.records = records

    def recv(self):
        if self.hasmore:
            self.recv_many()
        else:
            self.recv_single()

class GetNextReq(request):
    code = "0"
    paramlist = []

class GetNextResp(response):
    hasmore = 0
    pass

class LoginReq(request):
    code = "6011"
    paramlist = []

class LoginResp(response):
    okfieldn = 12
    hasmore = 0

class TradeCapInfoReq(request):
    code = "6012"
    paramlist = ["date", "currency"]

class TradeCapInfoResp(response):
    okfieldn = 26
    hasmore = 0

class QueryHQReq(request):
    code = "6017"
    paramlist = ["exchcode", "code"]

class QueryHQResp(response):
    okfieldn = 25
    hasmore = 0

class QueryOrderReq(request):
    code = "6020"
    paramlist = ["order_id", "seat"]

class QueryOrderResp(response):
    okfieldn = 10
    hasmore = 0

class GetClientNumReq(request):
    code = "6040"
    paramlist = ["exchcode", "seat"]

class GetClientNumResp(response):
    okfieldn = 5
    hasmore = 1

class GetContractReq(request):
    code = "6018"
    paramlist = []

class GetContractResp(response):
    okfieldn = 10
    hasmore = 1

class OrderReq(request):
    code = "6021"
    paramlist = ["exchcode", "code", "longshort", "openclose", "ifhedge", "count", "price", "tradenum", "seat"]

class OrderResp(response):
    okfieldn = 31
    hasmore = 0

class CancelOrderReq(request):
    code = "6022"
    paramlist = ["exchcode", "code", "longshort", "openclose", "ifhedge", "count", "price", "order_id", "cancelcount", "syscode", "seat", "orderseat"]

class CancelOrderResp(response):
    okfieldn = 13
    hasmore = 0

class QueryPosReq(request):
    code = "6014"
    paramlist = ["date"]

class QueryPosResp(response):
    okfieldn = 19
    hasmore = 1

class QueryAllOrderReq(request):
    code = "6019"
    paramlist = []

class QueryAllOrderResp(response):
    okfieldn = 33
    hasmore = 1
