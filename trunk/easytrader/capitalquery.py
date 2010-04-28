import jz
import socket
import sys
from datetime import datetime

# config
session_config = {}
session_config["tradedbfn"] = "tradeinfo.db"
session_config["jzserver"] = "172.18.20.52"
session_config["jzport"] = 9100
session_config["jzaccount"] = "85804530"
session_config["jzaccounttype"] = "Z"
session_config["jzpasswd"] = "123444"

s = jz.session(session_config)
if not s.setup():
    print "Cannot login"
    sys.exit(1)

cqreq = jz.CapitalQueryReq(s)
cqreq["user_code"] = s["user_code"]

#qoreq["order_id"] = "17063324"
# NOTE: use order_id in QueryOrderReq as biz_no in QueryOrder
#qoreq["biz_no"] = "17063331"
#qoreq["account"] = s["account"]

#qoreq["market"] = "00"
#qoreq["secu_acc"] = s["secu_acc"]["SH"]
#qoreq["secu_code"] = "601398"
#orderreq["trd_id"] = "0B"

#qoreq["market"] = "10"
#qoreq["order_id"] = "17063323"
cqreq.send()
print "request payload:", cqreq.payload

cqresp = jz.CapitalQueryResp(s)
cqresp.recv()
print "hasnext:", cqresp.hasnext
print cqresp.sections
for r in cqresp.records:
    print r
    print
print "retcode:", cqresp.retcode
print "retinfo:", cqresp.retinfo


