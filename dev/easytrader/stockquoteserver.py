import time
import pickle
import zlib
import datetime
import ConfigParser

from dbfpy import dbf
from quoteserver import QuotePusher, startserver
from genstockindex import genindex

class StockQuotePusher(QuotePusher):
    def setup(self, param):
        self.shdbfn = param["shdbfn"]
        self.szdbfn = param["szdbfn"]

        self.dbsh = dbf.Dbf(self.shdbfn, ignoreErrors=True, readOnly=True)
        self.dbsz = dbf.Dbf(self.szdbfn, ignoreErrors=True, readOnly=True)

        # genindex
        self.indexstockset = param["indexstockset"]
        self.shmap, self.szmap = genindex(self.indexstockset,
                self.shdbfn,
                self.szdbfn)
        if self.shmap is None or self.szmap is None:
            raise Exception("gen stock map failed.")

        self.starttime = datetime.time(9, 15, 00)
        self.endtime = datetime.time(15, 15, 00)
        now = datetime.datetime.now().time()
        if now > self.starttime and now < self.endtime:
            self.state = 1 # 1 for open
        else:
            self.state = 0 # 0 for close

    def updatequote(self):
        time.sleep(2)

        now = datetime.datetime.now().time()
        if now > self.starttime and now < self.endtime:
            if self.state == 0:
                self.logger.info("generating index for a new day!")
                self.shmap, self.szmap = genindex(self.indexstockset,
                        self.shdbfn,
                        self.szdbfn)
                if self.shmap is None or self.szmap is None:
                    raise Exception("gen stock map failed.")
            self.state = 1 # 1 for open
        else:
            self.state = 0 # 0 for close

        shreclist = []
        for scode in self.shmap:
            rec = self.dbsh[self.shmap[scode]]
            shreclist.append(rec)

        szreclist = []
        for scode in self.szmap:
            rec = self.dbsz[self.szmap[scode]]
            szreclist.append(rec)

        quoteinfo = {"SH":shreclist, "SZ":szreclist}

        price = pickle.dumps(quoteinfo, -1)
        price = zlib.compress(price)
        return price

if __name__=="__main__":
    configfn = "stockquoteserver.cfg"
    config = ConfigParser.RawConfigParser()
    config.read(configfn)
    MYSEC = "quoteserver"
    param = {}

    param["shdbfn"] = config.get(MYSEC, "shdbfn")
    param["szdbfn"] = config.get(MYSEC, "szdbfn")
    param["indexstockset"] = config.get(MYSEC, "indexstockset")

    startserver(configfn, StockQuotePusher, param)

