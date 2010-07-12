import sys

import jz

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
sreq.send()

mktinforeq = jz.MarketinfoReq(s)
mktinforeq.send()

sresp = jz.StockQueryResp(s)

count = 0
while 1:
    header_len, header_left, payload = sresp.recv_single()
    count += 1
    print "recv round:", count
    sresp.updatefrom(header_left, payload)
    if sresp.hasnext == "1":
        req = jz.GetNextReq(s)
        req.send()
    else:
        break


mktinforesp = jz.MarketinfoResp(s)
mktinforesp.recv()
print mktinforesp.records

