import sys
import csv

import jz

session_config = {}
session_config["tradedbfn"] = "tradeinfo.db"
session_config["jzserver"] = "172.18.20.52"
session_config["jzport"] = 9100
session_config["jzaccount"] = "85804530"
session_config["jzaccounttype"] = "Z"
session_config["jzpasswd"] = "123444"

s = jz.session(session_config)
s.setup()

ptfn = sys.argv[1]
r = csv.reader(open(ptfn))
w = csv.writer(sys.stdout)

for row in r:
    sireq = jz.SecuInfoReq(s)
    mkt = row[0]
    code = row[1]
    if mkt == "SH":
        sireq["market"] = jz.SHAMARKET
    elif mkt == "SZ":
        sireq["market"] = jz.SZAMARKET
    sireq["secu_code"] = code
    sireq.send()
    siresp = jz.SecuInfoResp(s)
    siresp.recv()
    if siresp.retcode == "0":
        row.append(siresp.records[0][10])
        row.append(siresp.records[0][11])
        row.append(siresp.records[0][12] == "1")
    w.writerow(row)
