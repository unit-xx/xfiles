import sys
import csv

from easytrader_lib import OrderRecord, Portfolio

ptfn = sys.argv[1]
f = open(ptfn, "rb")
reader = csv.reader(f)
stockinfo = {}
stocklist = []
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
f.close()

tradefn = sys.argv[2]
f = open(tradefn, "rb")
reader = csv.reader(f)
for i in reader:
    scode = i[0].upper() + i[1]
    si = stockinfo[scode]

    orec = OrderRecord()
    orec["ordercount"] = si["count"]
    orec["dealcount"] = i[2]
    if orec["ordercount"] == orec["dealcount"]:
        orec["order_state"] = Portfolio.BUYSUCCESS
    else:
        orec["order_state"] = Portfolio.CANCELBUYSUCCESS
        print >> sys.stderr, "miss match count for %s" % scode
    try:
        orec["dealprice"] = "0.0"
        orec["dealamount"] = "0.0"
    except IndexError:
        pass
    si["pastbuy"].append(orec)

writer = csv.writer(sys.stdout)
for scode in stocklist:
    si = stockinfo[scode]
    writer.writerow([si["market"], si["code"],
                    si["count"],
                    repr(si["pastbuy"]),
                    repr(si["pastsell"])])
