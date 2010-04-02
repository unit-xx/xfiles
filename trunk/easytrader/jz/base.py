from binascii import crc32, unhexlify
from blowfish import Blowfish

"""
Maintains common fields in header, such as version, key, etc.
"""
class session:
    def __init__(self):
        self.data = {}
        self.data["version"] = "KDGATEWAY1.0"
        self.data["usercode"] = ""
        self.data["site"] = ""
        self.data["branch"] = ""
        self.data["channel"] = ""
        self.data["session_id"] = ""
        self.data["reserve1"] = ""
        self.data["reserve2"] = ""
        self.data["reserve3"] = ""
        self.data["workkey"] = ""

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

class request:
    def __init__(self, session):
        self.session = session
        # controls what attributes to send and in what sequence, each 
        # request should set attrlist explicitly.
        self.attrlist = []

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
                    self.session["session_id"],
                    self.session["reserve1"],
                    self.session["reserve2"],
                    self.session["reserve3"],
                    ""
                    )
                )

    def genpayload(self):
        return ""

    def send(self, conn):
        data = self.serialize()
        conn.sendall(data)

class response:
    def __init__(self):
        pass

    def check(self):
        raise NotImplementedError()

    def recv_n(self, conn, n):
        left = n
        content = []
        while 1:
            if left <= 0:
                break
            buf = conn.recv(left)
            content.append(buf)
            left = left - len(buf)

        return "".join(content)

    def recv(self, conn):
        # consider data in more than one responses
        # recv header len
        # recv full header
        # recv payload, may involve multple receives

        while 1: # recv until no more packages
            header_len = int(self.recv_n(conn, 5)[0:4])
            self.header_left = self.recv_n(conn, header_len - 5)
            i = self.header_left.find("|")
            self.payload = self.recv_n(conn, int(self.header_left[0:i]))
            # TODO: implement more packges receiving now
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

class LoginRequest(request):
    def genpayload(self):
        return "100|"

class LoginResponse(response):
    def decrypt_workkey(self):
        cipher = Blowfish("SZKINGDOM")
        return cipher.decrypt(unhexlify(self.records[0][0]))

class MarketinfoRequest(request):
    def genpayload(self):
        return "201|"
