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
session_config["jzaccount"] = ""
session_config["jzaccounttype"] = "Z"
session_config["jzpasswd"] = ""

s = jz.session(session_config)
if not s.setup():
    print "Cannot login"
    sys.exit(1)

ptfn = sys.argv[1]
f = open(ptfn, "rb")
r = csv.reader(f)
w = csv.writer(open(ptfn+".order", "wb"))

ordercount = 0
print time.time()
for i in r:
    if eval(i[5]) == False:
        orderreq = jz.SubmitOrderReq(s)
        orderreq["user_code"] = s["user_code"]
        if i[0].upper() == "SH":
            orderreq["market"] = "10"
            orderreq["secu_acc"] = s["secu_acc"]["SH"]
        else:
            orderreq["market"] = "00"
            orderreq["secu_acc"] = s["secu_acc"]["SZ"]
        orderreq["account"] = s["account"]
        orderreq["secu_code"] = i[1]
        orderreq["trd_id"] = "0B"
        orderreq["qty"] = i[2]
        orderreq["price"] = i[4]
        #print orderreq.params
        orderreq.send()
        ordercount = ordercount + 1
        #orderresp = jz.SubmitOrderResp(s)
        #orderresp.recv()
        #print orderresp.retcode
        #print orderresp.retinfo
        #print orderresp.records[0][1]

print "make %d orders" % ordercount
for c in range(ordercount):
    orderresp = jz.SubmitOrderResp(s)
    orderresp.recv()
    w.writerow([orderresp.retcode,
        orderresp.retinfo.encode("GBK"),
        orderresp.records[0][1]])

print time.time()
print "done"
