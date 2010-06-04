import sys, datetime, jsd

session_config = {}
session_config["tradedbfn"] = "tradeinfo.db"
session_config["jsdserver"] = "172.18.20.71"
session_config["jsdport"] = 17990
session_config["jsdaccount"] = "9201"
session_config["jsdpasswd"] = "123"
session_config["branchcode"] = ""
session_config["ordermethod"] = ""
session_config["cffexcode"] = "G"

# login
s = jsd.session(session_config)
if not s.setup():
    print "Cannot login"
    sys.exit(1)

qdreq = jsd.QueryDealReq(s)
qdreq.send()
qdresp = jsd.QueryDealResp(s)
qdresp.recv()
for r in qdresp.records:
    print r
    print
print len(qdresp.records[0])

