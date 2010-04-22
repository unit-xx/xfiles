# -*- coding: GBK -*-

import jz
import socket

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

# query capital info
cqreq = jz.CapitalQueryReq(s)
cqreq["user_code"] = s["user_code"]
#cqreq["currency"] = "0"
cqreq.send()
cqresp = jz.CapitalQueryResp(s)
cqresp.recv()

# 买一手（？）工商银行
orderreq = jz.SubmitOrderReq(s)
orderreq["user_code"] = s["user_code"]
orderreq["market"] = "10"
orderreq["secu_acc"] = s["secu_acc"]["SH"]
orderreq["account"] = s["account"]
orderreq["secu_code"] = "601398"
orderreq["trd_id"] = "0B"
orderreq["price"] = "6.00"
orderreq["qty"] = "100"
orderreq.send()
orderresp = jz.SubmitOrderResp(s)
orderresp.recv()
s.storetrade(orderreq, orderresp)
print orderresp.retcode
print orderresp.retinfo
