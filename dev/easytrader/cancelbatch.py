# -*- coding: utf-8 -*-

import socket
import sys
import csv
import time
import jz

session_config = {}
session_config["tradedbfn"] = "tradeinfo.db"
session_config["jzserver"] = "172.18.12.205"
session_config["jzport"] = 9100
session_config["jzaccount"] = "36821529"
session_config["jzaccounttype"] = "Z"
session_config["jzpasswd"] = "100188"

s = jz.session(session_config)
if not s.setup():
    print "Cannot login"
    sys.exit(1)

ptfn = sys.argv[1]
f = open(ptfn, "rb")
r = csv.reader(f)
w = csv.writer(sys.stdout)

ordercount = 0
for i in r:
    coreq = jz.CancelOrderReq(s)
    coreq["user_code"] = s["user_code"]
    if i[2][0] == "B":
        coreq["market"] = "00"
    else:
        coreq["market"] = "10"
    coreq["order_id"] = i[2]
    coreq.send()
    coresp = jz.CancelOrderResp(s)
    coresp.recv()
    w.writerow([coresp.retcode, coresp.retinfo.encode("GBK")])

