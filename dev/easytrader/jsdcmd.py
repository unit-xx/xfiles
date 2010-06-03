import sys
import time
import jsd

session_config = {}
session_config["tradedbfn"] = "tradeinfo.db"
session_config["jsdserver"] = "172.18.20.71"
session_config["jsdport"] = 17990
session_config["jsdaccount"] = "9201"
session_config["jsdpasswd"] = "123"
session_config["branchcode"] = ""
session_config["ordermethod"] = ""

# global control flag
cancelorder = False
doorder = True
if len(sys.argv) > 1:
    oid = sys.argv[1]
    doorder = False

# login
s = jsd.session(session_config)
if not s.setup():
    print "Cannot login"
    sys.exit(1)

tcinforeq = jsd.TradeCapInfoReq(s)
tcinforeq["date"] = "20100512"
tcinforeq.send()
tcinforesp = jsd.TradeCapInfoResp(s)
tcinforesp.recv()
print "TradeCapital"
print tcinforesp.records
print
# hq, order, cancelorder, orderinfo

#qcreq = jsd.GetContractReq(s)
#qcreq.send()
#qcresp = jsd.GetContractResp(s)
#qcresp.recv()
#print qcresp.records
#print len(qcresp.records)
#print

hqreq = jsd.QueryHQReq(s)
hqreq["exchcode"] = "G"
hqreq["code"] = "IF1006"
hqreq.send()
hqresp = jsd.QueryHQResp(s)
hqresp.recv()
print "HQ"
print hqresp.records
print

getcnreq = jsd.GetClientNumReq(s)
getcnreq["exchcode"] = jsd.CFFEXCODE
getcnreq.send()
getcnresp = jsd.GetClientNumResp(s)
getcnresp.recv()
print "client number"
print getcnresp.records
print

if doorder:
    oreq = jsd.OrderReq(s)
    oreq["exchcode"] = jsd.CFFEXCODE
    oreq["code"] = "IF1006"
    oreq["longshort"] = "0"
    oreq["openclose"] = "0"
    oreq["ifhedge"] = "0"
    oreq["count"] = "1"
    oreq["price"] = "2855.21"
    oreq["clientnum"] = s["clientnum"]
    oreq["seat"] = s["seat"]

    #oreq["tradenum"] = "aaaaaaaaa9201a"
    oreq.send()
    oresp = jsd.OrderResp(s)
    oresp.recv()
    print "order response"
    print oresp.records
    print
    #print len(oresp.records[0])

qoreq = jsd.QueryOrderReq(s)
if doorder:
    qoreq["order_id"] = oresp.records[0][1]
else:
    qoreq["order_id"] = oid
qoreq.send()
qoresp = jsd.QueryOrderResp(s)
qoresp.recv()
print "order query"
for r in qoresp.records:
    print r
    print
print len(qoresp.records[0])
print

if cancelorder:
    coreq = jsd.CancelOrderReq(s)
    coreq["exchcode"] = "G"
    coreq["code"] = "IF1006"
    coreq["buysell"] = "0"
    coreq["openclose"] = "0"
    coreq["ifhedge"] = "0"
    coreq["count"] = "2"
    coreq["price"] = "2800"
    coreq["order_id"] = oid
    coreq["cancelcount"] = "2"
    coreq["syscode"] = "0"
    coreq.send()
    coresp = jsd.CancelOrderResp(s)
    coresp.recv()
    print "cancel order"
    print coresp.anwser
    print coresp.records
    print len(coresp.records[0])
    print

# $Id$
