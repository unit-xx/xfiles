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
        os.environ["PATH"] = "".join([os.environ["PATH"], ";", self.jsdcfg["hqdllpath"]])
        dll = WinDLL(self.jsdcfg["hqdll"])
        prototype = WINFUNCTYPE(c_bool, c_ushort, c_char_p)
        KSFTHQPUB_Start = prototype(("KSFTHQPUB_Start", dll))

        prototype = WINFUNCTYPE(None)
        KSFTHQPUB_Stop = prototype(("KSFTHQPUB_Stop", dll))

        prototype = WINFUNCTYPE(c_int, c_char_p, c_int, c_int, c_char_p)
        KSFTHQPUB_GetQuota = prototype(("KSFTHQPUB_GetQuota", dll))

        errmsg = create_string_buffer(1024)
        ret = KSFTHQPUB_Start(int(self.jsdcfg["hqport"]), errmsg)
        if not ret:
            self.logger.warning("Error while start receiving hq: %s", errmsg)
            raise Exception("Cannot start receiving hq")

    def getsindexprice(qdata, qcount):
        pass

    def updatequote(self):
        timeout = 2000 # 2sec
        MAX_QUOTA_ITEM_COUNT = 50
        quotaData = (jsdhq.KSFT_QUOTA_PUBDATA_ITEM * MAX_QUOTA_ITEM_COUNT)()
        while self.runflag:
            qcount = KSFTHQPUB_GetQuota(cast(quotaData, c_char_p),
                    sizeof(jsdhq.KSFT_QUOTA_PUBDATA_ITEM)*MAX_QUOTA_ITEM_COUNT,
                    timeout,
                    errmsg)
            if qcount < 0:
                self.logging.warning("Error while receiving hq: %s", errmsg)
            elif qcount > 0:
                data = self.getsindexprice(quotaData, qcount)
            else:
                pass

        quoteinfo = {"SH":shreclist, "SZ":szreclist}

        price = pickle.dumps(quoteinfo, -1)
        print len(price)
        price = zlib.compress(price)
        print len(price)
        print
        return price

if __name__=="__main__":
    configfn = "sindexquoteserver.cfg"
    config = ConfigParser.RawConfigParser()
    config.read(configfn)
    MYSEC = "quoteserver"
    param = {}

    param["hqport"] = config.get(MYSEC, "hqport")

    startserver(configfn, StockQuotePusher, param)

