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

sreq = jz.StockQueryReq(s)
sreq["user_code"] = s["user_code"]
sreq["secu_code"] = "601398"
sreq["market"] = "10"
sreq.send()
sresp = jz.StockQueryResp(s)
sresp.recv()
print sresp.sections
for r in sresp.records:
    print r
    print
print sresp.hasnext
print sresp.retcode
print sresp.retinfo.encode("GBK")
