from binascii import crc32, unhexlify, hexlify
from blowfish import Blowfish
from datetime import datetime
import sqlite3 as db

def pad(s, length, padder=" "):
    return s + "".join([padder * (length-len(s))])

"""
Maintains common fields in header, such as version, key, etc.
"""
class session:
    def __init__(self, conn, tradedbfn):
        # header fields
        self.data = {}
        self.data["version"] = "KDGATEWAY1.0"
        self.data["user_code"] = ""
        self.data["site"] = ""
        self.data["branch"] = ""
        self.data["channel"] = ""
        self.data["session"] = ""
        self.data["reserve1"] = ""
        self.data["reserve2"] = ""
        self.data["reserve3"] = ""
        self.data["workkey"] = ""
        self.data["secu_acc"] = {"SH":"", "SZ":""}

        # network connection
        self.conn = conn

        # db connections
        self.tradedbfn = tradedbfn
        self.tradedbconn = db.connect(tradedbfn)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

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

    def storetrade(self, reqpayload, resppayload):
        # TODO: not only raw
        t = datetime.now()
        self.tradedbconn.execute('insert into rawtradeinfo values (?, ?, ?)',
                (str(t),
                    reqpayload.decode("GBK"),
                    resppayload.decode("GBK")))
        self.tradedbconn.commit()

    def close(self):
        self.tradedbconn.commit()
        self.tradedbconn.close()
        self.conn.close()

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
        crc = "%08x|" % (c & 0xffffffff)

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
        params = "|".join([self[k] for k in self.paramlist])
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

    def recv_single(self):
        header_len = int(self.recv_n(5)[0:4])
        header_left = self.recv_n(header_len - 5)
        i = header_left.find("|")
        payload = self.recv_n(int(header_left[0:i]))
        return header_len, header_left, payload

    def recv(self):
        header_len, self.header_left, self.payload = self.recv_single()
        self.deserialize()
        if self.hasnext == "1":
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

        header_len, self.header_left, payload = self.recv_single()
        self.deserialize_headerleft()
        if self.hasnext:
            payload_list = [payload]
            noerr = True
            while 1:
                # do it
                req = GetNextReq(s)
                req.send()
                resp = GetNextResp(s)
                x, y, z = resp.recv_single()
                resp.deserialize_headerleft()
                # TODO: error case
                if(resp.retcode == 0 and resp.checkcrc() == True):
                    payload_list.append(resp.payload)
                else:
                    noerr = False
                    break
                if(resp.hasnext):
                    break
            if noerr:
                payload = "".join(payload_list)
            else:
                payload = ""
                self.retcode = -1

        self.payload = payload

    def deserialize_headerleft(self):
        tmp = self.header_left[0:-1].split("|")
        self.crc = tmp[1]
        self.version = tmp[2]
        self.retcode = tmp[3]
        self.retinfo = tmp[4].decode("GBK")
        self.hasnext = tmp[5]
        self.sectionnumber = int(tmp[6])
        self.recordnumber = int(tmp[7])

    def deserialize(self):
        # parse payload as an array of array, first line is section names.
        # implemented by sub-responses
        # TODO: check crc
        # TODO: check return code is success or not
        self.deserialize_headerleft()

        tmp = self.payload[0:-1].split("|")
        self.sections = tmp[0:self.sectionnumber]
        self.records = []
        start = self.sectionnumber
        end = start + self.sectionnumber
        for i in range(self.recordnumber):
            r = tmp[start:end]
            self.records.append(r)
            start = start + self.sectionnumber
            end = end + self.sectionnumber

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
        self.session["channel"] = "4"
        self.session["session"] = self.records[0][7]
        for r in self.records:
            if r[0] == "00":
                self.session["secu_acc"]["SZ"] = r[1]
            if r[0] == "10":
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
    # TODO: return multiple line?
    code = "510"
    paramlist = ["user_code", "market", "order_id"]

class QueryOrderResp(response):
    pass
