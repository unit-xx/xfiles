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
coreq["cancelcount"] = 
