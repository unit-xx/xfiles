from datetime import datetime
import logging
import socket
import sqlite3 as db
import win32com.client

HSVERSION = '3.13'

#TODO: constant definitions here.
#TODO: common fields vs. fields per request
#TODO: fill interface in request
#TODO: common field names, so that hs/jz switch is smooth.

"""
Maintains connections, common fields in header.
"""
class session:
    def __init__(self, config):
        self.initheader()
        self.config = config
        self.logger = logging.getLogger()
        self.tradedbconn = None
        self.hs = None

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def initheader(self):
        self.data = {}
        self.data["version"] = HSVERSION
        self.data["branchno"] = self.config['branchno']

    def setup(self):
        try:
            hs = win32com.client.Dispatch("HsCommX.Comm")
            hs.CreateX(0)
            ret = hs.ConnectX(self.config['protocol'],
                    self.config['servaddr'],
                    self.config['port'],
                    self.config['keyciper'],
                    self.config['key'],
                    len(self.config['key']))
            if ret == 0:
                self.hs = hs
            return (ret == 0)
        except pywintypes.com_error:
            return False

        # TODO: test password

    def storetrade(self, req, resp):
        return
        #t = datetime.now()
        #self.tradedbconn.execute('insert into rawtradeinfo
        #        values (?, ?, ?, ?)',
        #        (str(t),
        #            req.payload.decode("GBK"),
        #            resp.payload.decode("GBK"),
        #            "%s:%s" % (resp.retcode, resp.retinfo)
        #            ))
        #self.tradedbconn.commit()

    def close(self):
        if self.tradedbconn:
            self.tradedbconn.commit()
            self.tradedbconn.close()
            self.tradedbconn = None
        if self.hs:
            self.hs.DisConnect()
            self.hs = None

class request:
    # request code
    code = ""
    # controls what attributes to send and in what sequence, each 
    # request should set paramlist explicitly.
    paramlist = []
    # some required params are stored in sessionparams. If
    # needed, read by self.session['<key>']
    sessionparams = []
    # NOTE: 1. param key is different with corresponded key in config
    # 2. fill blank for unspecified keys? or just ignore

    def __init__(self, session):
        self.session = session
        # attribute values
        self.params = {}
        self.errorno = 0
        self.errormsg = ''

    def __getitem__(self, key):
        try:
            return self.params[key]
        # in case a param is not set, we assume it is empty
        except KeyError:
            return ""

    def __setitem__(self, key, value):
        self.params[key] = value

    def serialize(self):
        hs = self.session.hs

        hs.SetHead(self.session['branchno'], self.code)
        hs.SetRange(len(self.paramlist), 1)

        pkeys = self.params.keys()
        for p in self.pkeys:
            hs.AddField(p)

        for p in self.pkeys:
            if p in self sessionparams:
                hs.AddValue(self.session[k])
            else:
                hs.AddValue(self.params[k])

    def send(self):
        hs = self.session.hs
        self.serialize()
        ret = hs.Send()
        if ret != 0:
            self.errorno = ret
            self.errormsg = hs.ErrorMsg
        return ret

class response:
    def __init__(self, session):
        # TODO: define common field
        # NOTE: errorno/errorinfo is not listed in success responses
        self.session = session
        self.records = []
        self.errorno = 0
        self.errormsg = ''

    def recv(self):
        hs = self.session.hs

        self.session.hs.freepack()
        ret = hs.Receive()
        self.errorno = hs.errorno
        self.errormsg = hs.ErrorMsg
        if ret == 0:
            if hs.errorno == 0:
                # normal deserialzie
                fields = []
                for i in range(hs.Fieldcount):
                    fields.append(hs.GetFieldName(i))

                while 1:
                    if hs.Eof != 0:
                        break
                    tmp = {}
                    for f in fields:
                        tmp[f] = hs.Fieldbyname(f)
                    self.records.append(tmp)
                    hs.Moveby(1)
            else:
                # request error
                ret = hs.errorno

        return ret

class LoginReq(request):
    code = 200
    paramlist = ["idtype", "id", "passwd"]

class LoginResp(response):
    def updatesession(self):
        self.session["account"] = self.records[0][3]
        self.session["user_code"] = self.records[0][4]
        self.session["branch"] = self.records[0][6]
        self.session["session"] = self.records[0][7]
        assert len(self.records) >= 2
        for r in self.records:
            if r[0] == SZAMARKET:
                self.session["secu_acc"]["SZ"] = r[1]
            if r[0] == SHAMARKET:
                self.session["secu_acc"]["SH"] = r[1]
        assert(self.session["secu_acc"]["SZ"] != "")
        assert(self.session["secu_acc"]["SH"] != "")

class CapitalQueryReq(request):
    code = "502"
    paramlist = ["user_code", "user_roles", "account", "currency"]

class CapitalQueryResp(response):
    pass
