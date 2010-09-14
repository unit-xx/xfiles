# -*- coding: utf-8 -*-

import sys
import csv

from easytrader_lib import OrderRecord, Portfolio, SIndexRecord

stockinfo = {}
stocklist = []
sindexinfo = {}

tradefn = sys.argv[1]
f = open(tradefn, "rb")
reader = csv.reader(f)
for i in reader:
    if i[0] in ("SH", "SZ"):
        scode = i[0].upper() + i[1]
        stocklist.append(scode)
        stockinfo.setdefault(scode, {})
        si = stockinfo[scode]
        si["market"] = i[0].upper()
        si["code"] = i[1]
        si["count"] = i[2]
        si["pastbuy"] = []
        si["pastsell"] = []

        orec = OrderRecord()
        orec["ordercount"] = si["count"]
        orec["dealcount"] = si["count"]
        orec["order_state"] = Portfolio.BUYSUCCESS
        orec["dealprice"] = "0.0"
        orec["dealamount"] = "0.0"
        si["pastbuy"].append(orec)
    elif i[0] in ("IF"):
        sindexinfo["code"] = i[1].upper()

        sindexinfo["count"] = i[2]
        sindexinfo["state"] = Portfolio.IFOPENSHORTOK
        sindexinfo["pastopen"] = []
        r = SIndexRecord()
        r["order_id"] = "deadface"
        r["ordercount"] = sindexinfo["count"]
        r["openclose"] = "0"
        r["longshort"] = "1"
        r["ifhedge"] = "0"
        sindexinfo["pastopen"].append(r)
        sindexinfo["pastclose"] = []
        sindexinfo["deals"] = {}
        sindexinfo["deals"]["deadface"] = [(int(sindexinfo["count"]), 0.0)]

writer = csv.writer(sys.stdout)
if sindexinfo:
    writer.writerow(["IF", sindexinfo["code"], sindexinfo["count"],
            sindexinfo["state"].encode("utf-8"),
            repr(sindexinfo["pastopen"]),
            repr(sindexinfo["pastclose"]),
            repr(sindexinfo["deals"])])

for scode in stocklist:
    si = stockinfo[scode]
    writer.writerow([si["market"], si["code"],
                    si["count"],
                    repr(si["pastbuy"]),
                    repr(si["pastsell"])])
writer.writerow(["BO",u"买入成功".encode("utf8")])
