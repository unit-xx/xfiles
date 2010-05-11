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
    def __init__(self, conn, dbfn):
        # header fields
        self.data = {}
        self.data["flag"] = "R"
        self.data["addr"] = ""
        self.data["serial"] = ""
        self.data["user"] = "9201"
        self.data["passwd"] = "123"

        # network connection
        self.conn = conn

        # db connections
        self.dbfn = dbfn
        self.dbconn = db.connect(dbfn)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def storetrade(self, reqpayload, resppayload):
        # TODO: not only raw
        t = datetime.now()
        self.dbconn.execute('insert into rawoptiontradeinfo values (?, ?, ?)',
                (str(t),
                    reqpayload.decode("GBK"),
                    resppayload.decode("GBK")))
        self.dbconn.commit()

    def close(self):
        self.dbconn.commit()
        self.dbconn.close()
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
        header = self.genheader()
        payload = self.genpayload()
        # return full data package
        return "".join( (header, payload) )

    def genheader(self):
        return "|".join(
                (
                    self.session["flag"],
                    self.session["addr"],
                    self.session["serial"],
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
    success_fieldcnt = 0
    failed_fieldcnt = 0

    def __init__(self, session):
        self.session = session

    def check(self):
        raise NotImplementedError()

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
        #A|||N|40106|席位未处于开盘状态--9201,IF1006,买,开,保,1,3678.0000,00028184,cffex,cjis|40106|
        # first receiv 4 fields (by counting "|"), we know it is ok or not, then receive all left fields.
        header_len = int(self.recv_n(5)[0:4])
        header_left = self.recv_n(header_len - 5)
        i = header_left.find("|")
        payload = self.recv_n(int(header_left[0:i]))
        return header_len, header_left, payload

    def recv(self):
        header_len, self.header_left, self.payload = self.recv_single()
        self.deserialize()

    def recv_all(self):
        # consider data in more than one responses
        # recv header len
        # recv full header
        # recv payload, may involve multple receives

        while 1: # recv until no more responses
            header_len = int(self.recv_n(5)[0:4])
            self.header_left = self.recv_n(header_len - 5)
            i = self.header_left.find("|")
            # TODO: implement more packges receiving now,
            # self.payload should be the concatenated results
            # of multiple responses
            self.payload = self.recv_n(int(self.header_left[0:i]))
            break

    def deserialize(self):
        # parse payload as an array of array, first line is section names.
        # implemented by sub-responses
        # TODO: check crc
        # TODO: check return code is success or not
        tmp = self.header_left[0:-1].split("|")
        self.crc = tmp[1]
        self.version = tmp[2]
        self.retcode = tmp[3]
        self.retinfo = tmp[4].decode("GBK")
        self.hasnext = int(tmp[5])
        self.sectionnumber = int(tmp[6])
        self.recordnumber = int(tmp[7])

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
        # TODO: update secu_code
        for r in self.records:
            if r[0] == "00":
                self.session["secu_acc"]["sz"] = r[1]
            if r[0] == "10":
                self.session["secu_acc"]["sh"] = r[1]
        assert(self.session["secu_acc"]["sz"] != "")
        assert(self.session["secu_acc"]["sh"] != "")

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
