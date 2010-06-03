import sys, datetime, jsd

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

coreq = jsd.CancelOrderReq(s)
coreq["exchcode"] = jsd.CFFEXCODE
coreq["code"] = "IF1006"
coreq["longshort"] = "1"
coreq["openclose"] = "0"
coreq["ifhedge"] = "0"
coreq["count"] = "49"
coreq["price"] = '2826.80'
coreq["order_id"] = '265'
coreq["cancelcount"] = "49"
coreq["syscenter"] = "0"
coreq["seat"] = 'cffex'
coreq["orderseat"] = '244901'
coreq.send()
coresp = jsd.CancelOrderResp(s)
coresp.recv()
print coresp.records

