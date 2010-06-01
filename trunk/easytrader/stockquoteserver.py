import time
import ConfigParser
import pickle
import zlib

from dbfpy import dbf
from quoteserver import QuotePusher, startserver
from genstockindex import genindex

class StockQuotePusher(QuotePusher):
    def setup(self, param):
        shdbfn = param["shdbfn"]
        szdbfn = param["szdbfn"]

        self.dbsh = dbf.Dbf(shdbfn, ignoreErrors=True, readOnly=True)
        self.dbsz = dbf.Dbf(szdbfn, ignoreErrors=True, readOnly=True)

        # genindex
        self.shmap, self.szmap = genindex(param["indexstockset"],
                shdbfn,
                szdbfn)
        if self.shmap is None or self.szmap is None:
            raise Exception("gen stock map failed.")

    def updatequote(self):
        time.sleep(1)
        reclist = []
        for scode in self.shmap:
            rec = self.dbsh[self.shmap[scode]]
            reclist.append(rec)

        for scode in self.szmap:
            rec = self.dbsz[self.szmap[scode]]
            reclist.append(rec)

        price = pickle.dumps(reclist, -1)
        print len(price)
        price = zlib.compress(price)
        print len(price)
        print
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

