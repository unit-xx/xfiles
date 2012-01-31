# -*- coding: utf-8 -*-

import jz
import socket
import sys
import time

def readbatch(f):
    s = []
    for line in f:
        line = line.strip().split(",")
        if len(line) == 6 and eval(line[5]) == False:
            s.append([line[1], line[4], line[2]])
    return s

session_config = {}
session_config["tradedbfn"] = "tradeinfo.db"
session_config["jzserver"] = "172.18.12.205"
session_config["jzport"] = 9100
session_config["jzaccount"] = "36825141"
session_config["jzaccounttype"] = "Z"
session_config["jzpasswd"] = "111519"

s = jz.session(session_config)
if not s.setup():
    print "Cannot login"
    sys.exit(1)

#stocks = [
#        ["688888", "2.70", "100"],
#        ["677777", "2.70", "100"],
#        ]

stocks = [
        ["000111", "1.00", "100"],
        ]

#stocks = [
#        ["601288", "2.70", "100"],
#        ["601398", "4.20", "100"],
#        ["601939", "4.80", "100"],
#        ["601988", "3.50", "100"],
#        ["601328", "6.20", "100"],
#        ]

#stocks = [
#        ["000488", "7.80", "100"],
#        ["000002", "8.60", "100"],
#        ]
#f = open(sys.argv[1])
#stocks = readbatch(f)
print len(stocks), "stocks"
#sys.exit(1)

# buy the stocks
boreq = jz.BatchOrderReq(s)
boreq["account"] = s["account"]
boreq["customer"] = s["user_code"]
boreq["market"] = jz.SZAMARKET
boreq["board"] = "0"
boreq["secu_acc"] = s["secu_acc"]["SZ"]
boreq["trd_id"] = "0B"
boreq["price_msg"] = boreq.genorder(stocks)
print "price msg", (boreq["price_msg"])
print "price msg len", len(boreq["price_msg"])
t1 = time.time()
#sys.exit(1)
boreq.send()
boresp = jz.BatchOrderResp(s)
#print "|"+s.conn.read(5)+"|"
boresp.recv()
print boresp.records
t2 = time.time()
print "order time:", t2-t1

#print boresp.retcode
#print boresp.retinfo
print len(boresp.records)
#print boresp.records
print
bid = boresp.records[0][0]
#oid = boresp.records[0][1]
# query an order

sys.exit(1)
time.sleep(1)

# cancel them all
bcreq = jz.BatchCancelReq(s)
bcreq["account"] = s["account"]
bcreq["customer"] = s["user_code"]
bcreq["market"] = jz.SZAMARKET
bcreq["board"] = "0"
bcreq["biz_no"] = bid
t1 = time.time()
bcreq.send()
bcresp = jz.BatchCancelResp(s)
bcresp.recv()
t2 = time.time()
print "cancel time", t2-t1

print bcresp.retcode
print bcresp.retinfo
print len(bcresp.records)
print bcresp.records

# query an order

# cancel one

# query an order
