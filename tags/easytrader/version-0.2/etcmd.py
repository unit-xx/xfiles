# -*- coding: utf-8 -*-

import jz
import socket
import sys

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

mktinforeq = jz.MarketinfoReq(s)
mktinforeq.send()
mktinforesp = jz.MarketinfoResp(s)
mktinforesp.recv()
#s.storetrade(mktinforeq, mktinforesp)

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
orderreq["price"] = "5.00"
orderreq["qty"] = "100"
orderreq.send()
orderresp = jz.SubmitOrderResp(s)
orderresp.recv()
s.storetrade(orderreq, orderresp)
print orderresp.retcode
print orderresp.retinfo
print orderresp.records[0][1]

sys.exit(1)

orderreqjsyh = jz.SubmitOrderReq(s)
orderreqjsyh["user_code"] = s["user_code"]
orderreqjsyh["market"] = "10"
orderreqjsyh["secu_acc"] = s["secu_acc"]["SH"]
orderreqjsyh["account"] = s["account"]
orderreqjsyh["secu_code"] = "601939"
orderreqjsyh["trd_id"] = "0B"
orderreqjsyh["price"] = "5.70"
orderreqjsyh["qty"] = "100"
orderreqjsyh["biz_no"] = orderresp.records[0][1]
orderreqjsyh.send()
orderrespjsyh = jz.SubmitOrderResp(s)
orderrespjsyh.recv()
s.storetrade(orderreqjsyh, orderrespjsyh)

orderreqzgyh = jz.SubmitOrderReq(s)
orderreqzgyh["user_code"] = s["user_code"]
orderreqzgyh["market"] = "10"
orderreqzgyh["secu_acc"] = s["secu_acc"]["SH"]
orderreqzgyh["account"] = s["account"]
orderreqzgyh["secu_code"] = "601988"
orderreqzgyh["trd_id"] = "0B"
orderreqzgyh["price"] = "5.70"
orderreqzgyh["qty"] = "100"
orderreqzgyh["biz_no"] = orderresp.records[0][1]
orderreqzgyh.send()
orderrespzgyh = jz.SubmitOrderResp(s)
orderrespzgyh.recv()
s.storetrade(orderreqzgyh, orderrespzgyh)
