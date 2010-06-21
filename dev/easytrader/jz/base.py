from binascii import crc32, unhexlify, hexlify
from blowfish import Blowfish
from datetime import datetime
import logging
import socket
import sqlite3 as db

def pad(s, length, padder=" "):
    return s + "".join([padder * (length-len(s))])

SHAMARKET = "10"
SZAMARKET = "00"
"""
Maintains common fields in header, such as version, key, etc.
"""
class session:
    #def __init__(self, conn, tradedbfn):
    #    # header fields
    #    self.initheader()

    #    # network connection
    #    self.conn = conn

    #    # db connections
    #    self.tradedbfn = tradedbfn

    def __init__(self, sessioncfg):
        self.initheader()
        self.sessioncfg = sessioncfg
        self.logger = logging.getLogger()
        self.tradedbconn = None
        self.conn = None

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def initheader(self):
        self.data = {}
        self.data["version"] = "KDGATEWAY1.0"
        self.data["user_code"] = ""
        self.data["site"] = socket.gethostbyname(socket.gethostname())
        self.data["branch"] = ""
        self.data["channel"] = ""
        self.data["session"] = ""
        self.data["reserve1"] = "1"
        self.data["reserve2"] = ""
        self.data["reserve3"] = ""
        self.data["workkey"] = "88888888"
        self.data["secu_acc"] = {"SH":"", "SZ":""}

    def setup(self):
        try:
            c = socket.socket()
            c.connect((self.sessioncfg["jzserver"], self.sessioncfg["jzport"]))
            self.conn = c

            self.tradedbconn = db.connect(self.sessioncfg["tradedbfn"], timeout=30)
        except socket.error:
            self.close()
            return False

        try:
            cireq = CheckinReq(self)
            cireq.send()
            ciresp = CheckinResp(self)
            ciresp.recv()
            if ciresp.retcode != "0":
                # TODO: change this and two following print to return code or myexception
                self.logger.warning("Checkin failed: %s, %s" %
                        (loginresp.retcode, loginresp.retinfo))
                return False
            # update workkey
            self["workkey"] = ciresp.getworkkey()

            loginreq = LoginReq(self)
            loginreq["idtype"] = self.sessioncfg["jzaccounttype"]
            loginreq["id"] = self.sessioncfg["jzaccount"]
            loginreq["passwd"] = self.encrypt(pad(self.sessioncfg["jzpasswd"],
                (len(self.sessioncfg["jzpasswd"])/8+1)*8))
            loginreq.send()
            loginresp = LoginResp(self)
            loginresp.recv()
            # update session fields from login response
            if loginresp.retcode != "0":
                self.logger.warning("Login failed: %s, %s" %
                        (loginresp.retcode, loginresp.retinfo))
                return False

            loginresp.updatesession()
            self.logger.info("Login ok")
            return True
        except socket.error:
            self.close()
            return False

    def encrypt(self, s):
        assert(len(s) % 8 == 0)
        cipher = Blowfish(self["workkey"])
        tmp = []
        for i in range(0, len(s), 8):
            tmp.append(cipher.encrypt(s[i:i+8]))
            # it is IMPORTANT to convert the encrypted code into UPPER case.
        return hexlify("".join(tmp)).upper()

    def decrypt(self, s):
        pass

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
        if self.tradedbconn:
            self.tradedbconn.commit()
            self.tradedbconn.close()
            self.tradedbconn = None
        if self.conn:
            self.conn.close()
            self.conn = None

class request:
    # request code
    code = ""
    # controls what attributes to send and in what sequence, each 
    # request should set paramlist explicitly.
    paramlist = []

    def __init__(self, session):
        self.session = session
        # attribute values
        self.params = {}

    def __getitem__(self, key):
        try:
            return self.params[key]
        # in case a param is not set, we assume it is empty
        except KeyError: 
            return ""

    def __setitem__(self, key, value):
        self.params[key] = value

    def check(self):
        raise NotImplementedError()

    def serialize(self):
        # a request is splitted into:
        # (header)(payload)
        # (header) = (header_len, payload_len, crc, headerP)
        # headerP for header prime, contains version, user code, etc.

        # gen payload, each sub-request implement it separately
        payload = self.genpayload()
        self.payload = payload

        # gen header without headerP
        headerP = self.genheaderP()
        header_len = "%04d|" % (19 + len(headerP))
        payload_len = "%04d|" % len(payload)
        crc = "%s|" % self.session["workkey"]

        # calc crc
        c = 0
        c = crc32(header_len, c)
        c = crc32(payload_len, c)
        c = crc32(crc, c)
        c = crc32(headerP, c)
        c = crc32(payload, c)
        crc = "%x" % (c & 0xffffffff)
        #if len(crc) < 8:
        #    print "!!"
        crc = "%s%s|" % (crc, "0" * (8 - len(crc)))

        # return full data package
        return "".join( (header_len, payload_len, crc, headerP, payload) )

    def genheaderP(self):
        return "|".join(
                (
                    self.session["version"],
                    self.session["user_code"],
                    self.session["site"],
                    self.session["branch"],
                    self.session["channel"],
                    self.session["session"],
                    self.session["reserve1"],
                    self.session["reserve2"],
                    self.session["reserve3"],
                    ""
                    )
                )

    def genpayload(self):
        # reqcode|(params|)+
        params = "|".join([str(self[k]) for k in self.paramlist])
        return "|".join([self.code, params, ""])

    def send(self):
        data = self.serialize()
        self.session.conn.sendall(data)

class response:
    def __init__(self, session):
        self.session = session

    def checkcrc(self):
        # TODO: implement it
        return True

    def recv_n(self, n):
        left = n
        content = []
        while 1:
            if left <= 0:
                break
            buf = self.session.conn.recv(left)
            content.append(buf)
            left = left - len(buf)

        return "".join(content)

    def recv_single1(self):
        header_len = int(self.recv_n(5)[0:4])
        #self.header_len = header_len
        header_left = self.recv_n(header_len - 5)
        i = header_left.find("|")
        payload_len = int(header_left[0:i])
        payload = self.recv_n(payload_len)
        return header_len, header_left, payload

    def recv_single2(self):
        tmp = self.recv_n(5+11)
        print tmp
        tmp = tmp.split("|")
        assert tmp[2] == ""
        header_len = int(tmp[0])
        payload_len = int(tmp[1])

        tmp = self.recv_n(header_len + payload_len - 16)
        header_left = tmp[0:header_len-16]
        payload = tmp[header_len-16:]
        return header_len, header_left, payload

    recv_single = recv_single1

    def recv_first(self):
        header_len, self.header_left, self.payload = self.recv_single()
        self.sections, self.records = self.deserialize()
        if self.hasnext == "1":
            # TODO: for debug only, comment this line after finish recv_all
            print "Has more results: %s" % type(self)

    def recv_all(self):
        # TODO: finish implementation
        # consider data in more than one responses
        # recv header len
        # recv full header
        # recv payload, may involve multple receives

        # recv until no more responses
        # any one retcode is not 0, all failed
        # any one crc failed, all failed

        self.records = []
        while 1:
            header_len, self.header_left, self.payload = self.recv_single()
            self.deserialize_headerleft()
            sections, records = self.deserialize_payload()
            self.records.extend(records)
            self.sections = sections

            if self.hasnext == "1":
                req = GetNextReq(self.session)
                req.send()
            else:
                break

    recv = recv_all

    def deserialize_headerleft1(self):
        tmp = self.header_left[0:-1].split("|")
        self.crc = tmp[1]
        self.version = tmp[2]
        self.retcode = tmp[3]
        self.retinfo = tmp[4].decode("GBK")
        self.hasnext = tmp[5]
        self.sectionnumber = int(tmp[6])
        self.recordnumber = int(tmp[7])

    def deserialize_headerleft2(self):
        tmp = self.header_left[0:-1].split("|")
        self.crc = tmp[0]
        self.version = tmp[1]
        self.retcode = tmp[2]
        self.retinfo = tmp[3].decode("GBK")
        self.hasnext = tmp[4]
        self.sectionnumber = int(tmp[5])
        self.recordnumber = int(tmp[6])

    deserialize_headerleft = deserialize_headerleft1

    def deserialize(self):
        # parse payload as an array of array, first line is section names.
        # implemented by sub-responses
        # TODO: check crc
        # TODO: check return code is success or not
        self.deserialize_headerleft()
        return self.deserialize_payload()

    def deserialize_payload(self):
        tmp = self.payload[0:-1].split("|")
        sections = tmp[0:self.sectionnumber]
        records = []
        start = self.sectionnumber
        end = start + self.sectionnumber
        for i in range(self.recordnumber):
            r = tmp[start:end]
            records.append(r)
            start = start + self.sectionnumber
            end = end + self.sectionnumber
        return sections, records

class CheckinReq(request):
    code = "100"
    paramlist = []

class CheckinResp(response):
    def getworkkey(self):
        cipher = Blowfish("SZKINGDOM")
        return cipher.decrypt(unhexlify(self.records[0][0]))

class GetNextReq(request):
    code = "99"
    paramlist = []

class GetNextResp(response):
    pass

class MarketinfoReq(request):
    code = "201"
    paramlist = ["market"]

class MarketinfoResp(response):
    pass

class LoginReq(request):
    code = "301"
    paramlist = ["idtype", "id", "passwd"]

class LoginResp(response):
    def updatesession(self):
        self.session["account"] = self.records[0][3]
        self.session["user_code"] = self.records[0][4]
        self.session["branch"] = self.records[0][6]
        self.session["channel"] = "2"
        self.session["session"] = self.records[0][7]
        assert len(self.records) == 2
        for r in self.records:
            if r[0] == SZAMARKET:
                self.session["secu_acc"]["SZ"] = r[1]
            if r[0] == SHAMARKET:
                self.session["secu_acc"]["SH"] = r[1]
        assert(self.session["secu_acc"]["SZ"] != "")
        assert(self.session["secu_acc"]["SH"] != "")

class CapitalQueryReq(request):
    code = "502"
    paramlist = ["user_code", "account", "currency"]

class CapitalQueryResp(response):
    pass

class MaxTradeQueryReq(request):
    code = "402"
    paramlist = ["user_code", "market", "secu_acc", "account", "secu_code", "trd_id", "price", "ext_inst"]

class MaxTradeQueryResp(response):
    pass

class SubmitOrderReq(request):
    code = "403"
    paramlist = ["user_code", "market", "secu_acc", "account", "seat", "secu_code", "trd_id", "price", "qty", "biz_no", "ext_inst", "ext_rec_num", "op_remark", "match_seat", "match_num"]
    pass

class SubmitOrderResp(response):
    pass

class QueryOrderReq(request):
    code = "505"
    paramlist = ["begin_date", "end_date", "get_orders_mode", "user_code", "market", "secu_acc", "secu_code", "trd_id", "biz_no", "order_id", "branch", "account", "ext_inst"]

class QueryOrderResp(response):
    def getTotal(self):
        dealcount = 0
        dealamount = 0.0
        dealprice = 0.0
        # calculate total deal count/amount
        if len(self.records) == 0:
            dealcount, dealamount, dealprice = None, None, None
        else:
            for r in self.records:
                dealcount = dealcount + int(r[22])
                dealamount = dealamount + float(r[24])
            try:
                dealprice = dealamount / dealcount
            except ZeroDivisionError:
                pass
        return dealcount, dealamount, dealprice


class DealReq(request):
    code = "506"
    paramlist = ["begin_date", "end_date", "user_code", "market", "secu_acc", "secu_code", "trd_id", "order_id", "branch", "account", "ext_inst"]

class DealResp(response):
    pass

class CancelOrderReq(request):
    code = "404"
    paramlist = ["market", "order_id", "account"]

class CancelOrderResp(response):
    pass

class StockQueryReq(request):
    # the stocks i hold
    code = "504"
    paramlist = ["user_code", "account", "market", "secu_acc", "secu_code", "ext_inst"]

class StockQueryResp(response):
    pass

class SecuInfoReq(request):
    code = "203"
    paramlist = ["market", "secu_cls", "secu_code"]

class SecuInfoResp(response):
    pass
