import jsd
import time

session_config = {}
session_config["tradedbfn"] = "tradeinfo.db"
session_config["jsdserver"] = "172.18.20.71"
session_config["jsdport"] = 17990
session_config["jsdaccount"] = "9201"
session_config["jsdpasswd"] = "123"
session_config["branchcode"] = ""
session_config["ordermethod"] = ""

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

