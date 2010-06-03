import sys, datetime, jsd
import time

session_config = {}
session_config["tradedbfn"] = "tradeinfo.db"
session_config["jsdserver"] = "172.18.20.71"
session_config["jsdport"] = 17990
session_config["jsdaccount"] = "9201"
session_config["jsdpasswd"] = "123"
session_config["branchcode"] = ""
session_config["ordermethod"] = ""

# login
s = jsd.session(session_config)
if not s.setup():
    print "Cannot login"
    sys.exit(1)

oreq = jsd.OrderReq(s)
oreq["exchcode"] = jsd.CFFEXCODE
oreq["code"] = "IF1006"
oreq["longshort"] = "0"
oreq["openclose"] = "1"
oreq["ifhedge"] = "0"
oreq["count"] = "50"
oreq["price"] = "2766.00"
oreq["clientnum"] = s["clientnum"]
oreq["seat"] = s["seat"]

#oreq["tradenum"] = "aaaaaaaaa9201a"
oreq.send()
oresp = jsd.OrderResp(s)
oresp.recv()
print "order response"
print oresp.records
print

time.sleep(1)

qoreq = jsd.QueryOrderReq(s)
try:
    qoreq["order_id"] = sys.argv[1]
except IndexError:
    qoreq["order_id"] = oresp.records[0][1]
qoreq.send()
qoresp = jsd.QueryOrderResp(s)
qoresp.recv()
print "order query"
print qoresp.records
print len(qoresp.records[0])
print

