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

pqreq = jsd.QueryPosReq(s)
today = datetime.datetime.today()
pqreq["date"] = "%d%02d%d" % (today.year, today.month, today.day)
pqreq.send()
pqresp = jsd.QueryPosResp(s)
pqresp.recv()
print "position info"
for r in pqresp.records:
    print r
    print
