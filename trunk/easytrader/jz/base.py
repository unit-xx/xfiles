from binascii import crc32, unhexlify
from blowfish import Blowfish
import binascii

"""
Maintains common fields in header, such as version, key, etc.
"""

def pad(s, length, padder=" "):
    return s + "".join([padder * (length-len(s))])

class session:
    def __init__(self, conn):
        # header fields
        self.data = {}
        self.data["version"] = "KDGATEWAY1.0"
        self.data["usercode"] = ""
        self.data["site"] = ""
        self.data["branch"] = ""
        self.data["channel"] = ""
        self.data["session"] = ""
        self.data["reserve1"] = ""
        self.data["reserve2"] = ""
        self.data["reserve3"] = ""
        self.data["workkey"] = ""

        # network connection
        self.conn = conn

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
        return binascii.hexlify("".join(tmp)).upper()

    def decrypt(self, s):
        pass

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
                    self.session["usercode"],
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

    def recv(self):
        # consider data in more than one responses
        # recv header len
        # recv full header
        # recv payload, may involve multple receives

        while 1: # recv until no more packages
            header_len = int(self.recv_n(5)[0:4])
            self.header_left = self.recv_n(header_len - 5)
            i = self.header_left.find("|")
            self.payload = self.recv_n(int(self.header_left[0:i]))
            # TODO: implement more packges receiving now
            break

        self.deserialize()

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

class MarketinfoReq(request):
    code = "201"
    paramlist = ["market"]

class MarketinfoResp(response):
    pass

class LoginReq(request):
    code = "301"
    paramlist = ["idtype", "id", "passwd"]

class LoginResp(response):
    pass

class CapitalQueryReq(request):
    code = "502"
    paramlist = ["usercode", "account", "currency"]

class CapitalQueryResp(response):
    pass

class MaxTradeQueryReq(request):
    code = "402"
    paramlist = ["usercode", "market", "secu_acc", "account", "secu_code", "trd_id", "price", "ext_inst"]

class MaxTradeQueryResp(response):
    pass
