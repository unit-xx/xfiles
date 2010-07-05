# -*- coding: utf-8 -*-

import jz
import sys

session_config = {}
session_config["tradedbfn"] = "tradeinfo.db"
#session_config["jzserver"] = "172.18.20.52"
session_config["jzserver"] = "172.18.12.205"
session_config["jzport"] = 9100
session_config["jzaccount"] = raw_input("account: ")
session_config["jzaccounttype"] = "Z"
session_config["jzpasswd"] = raw_input("password: ")

s = jz.session(session_config)
if not s.setup():
    print "Cannot login"
    sys.exit(1)

# 申购1000000（100万）份50etf（510051）
orderreq = jz.SubmitOrderReq(s)
orderreq["user_code"] = s["user_code"]
orderreq["market"] = "10"
orderreq["secu_acc"] = s["secu_acc"]["SH"]
orderreq["account"] = s["account"]
orderreq["secu_code"] = "510051"
orderreq["trd_id"] = "7K"
orderreq["price"] = "1.000"
orderreq["qty"] = "1000000"
orderreq.send()
orderresp = jz.SubmitOrderResp(s)
orderresp.recv()
print orderresp.retcode
print orderresp.retinfo
print orderresp.sections
print orderresp.records

