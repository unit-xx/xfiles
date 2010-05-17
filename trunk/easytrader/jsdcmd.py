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
print tcinforesp.records
# hq, order, cancelorder, orderinfo

hqreq = jsd.QueryHQReq(s)
#hqreq["exchcode"] = "G"
hqreq["code"] = "IF1005"
hqreq.send()
hqresp = jsd.QueryHQResp(s)
hqresp.recv()
print hqresp.records

getcnreq = jsd.GetClientNumReq(s)
getcnreq.send()
getcnresp = jsd.GetClientNumResp(s)
getcnresp.recv()
print getcnresp.records

doorder = True
if len(sys.argv) > 1:
    oid = sys.argv[1]
    doorder = False

if doorder:
    oreq = jsd.OrderReq(s)
    oreq["exchcode"] = "G"
    oreq["code"] = "IF1006"
    oreq["buysell"] = "0"
    oreq["openclose"] = "0"
    oreq["ifhedge"] = "0"
    oreq["count"] = "2"
    oreq["price"] = "2800"
    oreq["tradenum"] = "00028184"
    #oreq["tradenum"] = "aaaaaaaaa9201a"
    oreq.send()
    oresp = jsd.OrderResp(s)
    oresp.recv()
    print oresp.records
    #print len(oresp.records[0])

qoreq = jsd.QueryOrderReq(s)
if doorder:
    qoreq["order_id"] = oresp.records[0][1]
else:
    qoreq["order_id"] = oid
qoreq.send()
qoresp = jsd.QueryOrderResp(s)
qoresp.recv()
print qoresp.records
print len(qoresp.records[0])

cancelorder = True
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
    print coresp.anwser
    print coresp.records
    print len(coresp.records[0])
