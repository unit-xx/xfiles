from datetime import datetime
import logging
import socket
import sqlite3 as db
import win32com.client
import pywintypes

HSVERSION = '3.13'

# constant definitions here.
# exchange type
EXCH_SH = '1'
EXCH_SZ = '2'
EXCH_CFFEX = '5'

# entrust_way
ENTW_COUNTER = '4'

#TODO: common fields vs. fields per request
#TODO: fill interface in request
#TODO: common field names, so that hs/jz switch is smooth.

"""
Maintains connections, common fields in header.
"""
class session:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger()
        self.initheader()
        self.tradedbconn = None
        self.hs = None

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def initheader(self):
        self.data = {}
        # TODO: add project id
        # TODO: diff between tested and official hs interface
        self.data["version"] = HSVERSION
        self.data["branch_no"] = self.config['branch_no']
        self.data["l_op_code"] = self.config['l_op_code']
        self.data["vc_op_password"] = self.config['vc_op_password']
        self.data["op_entrust_way"] = self.config['op_entrust_way']
        self.data["op_station"] = self.config['op_station']
        self.data["fund_account"] = self.config['fund_account']
        self.data["account_content"] = self.config['fund_account']
        self.data["password"] = self.config['password']

    def setup(self):
        try:
            hs = win32com.client.Dispatch("HsCommX.Comm")
            hs.CreateX(0)
            ret = hs.ConnectX(self.config['protocol'],
                    self.config['hsserver'],
                    self.config['hsport'],
                    self.config['keyciper'],
                    self.config['key'],
                    len(self.config['key']))
            if ret == 0:
                self.hs = hs
            else:
                return False

            # try login and update account info
            loginreq = LoginReq(self)
            loginreq.send()
            loginresp = LoginResp(self)
            loginresp.recv()
            if loginresp.errorno != 0:
                self.logger.warning("Login failed: %s, %s" %
                        (loginresp.errorno, loginresp.errormsg))
                return False

            loginresp.updatesession()
            self.logger.info("Login ok")
            return True
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
    headerfield = ['version', 'l_op_code', 'vc_op_password', 'op_entrust_way', 'op_station', 'fund_account', 'password']
    headernum = len(headerfield)

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

        hs.SetHead(self.session['branch_no'], self.code)
        hs.SetRange(len(self.paramlist)+self.headernum, 1)

        self.addSessionSey()
        pkeys = self.paramlist
        for p in pkeys:
            hs.AddField(p)

        self.addSessionValue()
        for p in pkeys:
            hs.AddValue(self[p])

    def addSessionSey(self):
        hs = self.session.hs
        for f in self.headerfield:
            hs.AddField(f)

    def addSessionValue(self):
        hs = self.session.hs
        for f in self.headerfield:
            hs.AddValue(self.session[f])

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
        self.fields = []
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
                for i in range(hs.Fieldcount):
                    self.fields.append(hs.GetFieldName(i))

                while 1:
                    if hs.Eof != 0:
                        break
                    tmp = {}
                    for f in self.fields:
                        tmp[f] = hs.Fieldbyname(f)
                    self.records.append(tmp)
                    hs.Moveby(1)
            else:
                # request error
                ret = hs.errorno

        return ret

class LoginReq(request):
    code = 200
    paramlist = []
    headerfield = ['version', 'l_op_code', 'vc_op_password', 'op_entrust_way', 'op_station', 'account_content', 'password']
    headernum = len(headerfield)

class LoginResp(response):
    def updatesession(self):
        self.session["branch_no"] = self.records[0]['branch_no']
        self.session["client_name"] = self.records[0]['client_name']
        self.session["client_rights"] = self.records[0]['client_rights']

class QueryHistOrderReq(request):
    code = '421'
    paramlist = ['start_date', 'end_date', 'stock_code', 'request_num', 'position_str']

class QueryHistOrderResp(response):
    pass

class QueryTodayOrderReq(request):
    code = '401'
    paramlist = ['exchange_type', 'stock_code', 'locate_entrust_no', 'query_direction', 'sort_direction', 'request_num', 'position_str']

    def qone(self, entrust_no):
        self['locate_entrust_no'] = entrust_no
        self['request_num'] = '1'
        return self.send()

    def qall(self):
        return self.send()

class QueryTodayOrderResp(response):
    pass

class OrderReq(request):
    code = '302'
    paramlist = ['exchange_type', 'stock_account', 'stock_code', 'entrust_amount', 'entrust_price', 'entrust_prop', 'entrust_bs', 'c_bs', 'external_no', 'batch_no']

    def bsStock(self, exch, bs, scode, price, amount):
        if exch == 'SH':
            self['exchange_type'] = EXCH_SH
        elif exch == 'SZ':
            self['exchange_type'] = EXCH_SZ
        else:
            return -1

        self['stock_code'] = scode
        self['entrust_amount'] = amount
        self['entrust_price'] = price
        self['entrust_prop'] = '0'
        if bs == 'BUY':
            self['entrust_bs'] = '1'
        elif bs == 'SELL':
            self['entrust_bs'] = '2'
        else:
            return -1

        return self.send()

class OrderResp(response):
    pass

class TryBuyReq(request):
    code = '301'
    paramlist = ['exchange_type', 'stock_account', 'stock_code', 'entrust_price', 'entrust_prop', 'c_bs']

    def dotry(self, exch, scode, price):
        if exch == 'SH':
            self['exchange_type'] = EXCH_SH
        elif exch == 'SZ':
            self['exchange_type'] = EXCH_SZ
        else:
            return -1
        self['stock_code'] = scode
        self['entrust_price'] = price
        self['entrust_prop'] = '0'
        return self.send()

class TryBuyResp(response):
    pass

class CapitalQueryReq(request):
    code = "502"
    paramlist = ["user_code", "user_roles", "account", "currency"]

class CapitalQueryResp(response):
    pass
