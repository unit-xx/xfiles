import os
import time
import ConfigParser
import pickle
import zlib

from dbfpy import dbf
from quoteserver import QuotePusher, startserver
from genstockindex import genindex
import jsdhq
from ctypes import *

class SIndexQuotePusher(QuotePusher):

    def setup(self, param):
        os.environ["PATH"] = "".join([os.environ["PATH"], ";", param["hqdllpath"]])
        dll = WinDLL(param["hqdll"])
        prototype = WINFUNCTYPE(c_bool, c_ushort, c_char_p)
        self.KSFTHQPUB_Start = prototype(("KSFTHQPUB_Start", dll))

        prototype = WINFUNCTYPE(c_int, c_char_p, c_int, c_int, c_char_p)
        self.KSFTHQPUB_GetQuota = prototype(("KSFTHQPUB_GetQuota", dll))

        prototype = WINFUNCTYPE(None)
        self.KSFTHQPUB_Stop = prototype(("KSFTHQPUB_Stop", dll))

        self.MAX_QUOTA_ITEM_COUNT = 50
        self.quotaData = (jsdhq.KSFT_QUOTA_PUBDATA_ITEM * self.MAX_QUOTA_ITEM_COUNT)()

        self.errmsg = create_string_buffer(1024)
        ret = self.KSFTHQPUB_Start(int(param["hqport"]), self.errmsg)
        if not ret:
            self.logger.warning("Error while start receiving hq: %s", self.errmsg)
            raise Exception("Cannot start receiving hq")

    def getsindexprice(self, qdata, qcount):
        ret = []
        for i in range(qcount):
            qd = qdata[i]
            if qd.exchCode == "G" and qd.varity_code == "IF":
                ret.append(qd)
        return ret

    def updatequote(self):
        timeout = 2000 # 2sec
        quote = []

        qcount = self.KSFTHQPUB_GetQuota(cast(self.quotaData, c_char_p),
                sizeof(jsdhq.KSFT_QUOTA_PUBDATA_ITEM)*self.MAX_QUOTA_ITEM_COUNT,
                timeout,
                self.errmsg)
        if qcount < 0:
            self.logging.warning("Error while receiving hq: %s", self.errmsg)
        elif qcount > 0:
            quote = self.getsindexprice(self.quotaData, qcount)
        else:
            pass

        if quote == []:
            return None
        else:
            price = pickle.dumps(quote, -1)
            #print len(price)
            price = zlib.compress(price)
            #print len(price)
            #print
            return price

    def finalize(self):
        self.KSFTHQPUB_Stop()

if __name__=="__main__":
    configfn = "sindexquoteserver.cfg"
    config = ConfigParser.RawConfigParser()
    config.read(configfn)
    MYSEC = "quoteserver"
    param = {}

    param["hqport"] = config.get(MYSEC, "hqport")
    param["hqdll"] = config.get(MYSEC, "hqdll")
    param["hqdllpath"] = config.get(MYSEC, "hqdllpath")

    startserver(configfn, SIndexQuotePusher, param)

