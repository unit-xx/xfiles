# -*- coding: GBK -*-

import jz
import socket

# config
jzserver = "172.18.20.52"
jzport = 9100
dbfn = "tradeinfo.db"

# sign in system
conn = socket.socket()
conn.connect((jzserver, jzport))

s = jz.session(conn, dbfn)
cireq = jz.CheckinReq(s)
cireq.send()
ciresp = jz.CheckinResp(s)
ciresp.recv()
# update workkey
s["workkey"] = ciresp.getworkkey()

print "begin mktinfo"
mktinforeq = jz.MarketinfoReq(s)
mktinforeq.send()
mktinforesp = jz.MarketinfoResp(s)
mktinforesp.recv()
print "end mktinfo"
s.storetrade(mktinforeq.payload, mktinforesp.payload)

# login as user
jzaccount = "85804530"
jzaccounttype = "Z"
jzpasswd = "123444"

loginreq = jz.LoginReq(s)
loginreq["idtype"] = jzaccounttype
loginreq["id"] = jzaccount
loginreq["passwd"] = s.encrypt(jz.pad(jzpasswd, (len(jzpasswd)/8+1)*8))
loginreq.send()
loginresp = jz.LoginResp(s)
loginresp.recv()

# update session fields from login response
if loginresp.retcode == "0":
    loginresp.updatesession()

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
orderreq["secu_acc"] = s["secu_acc"]["sh"]
orderreq["account"] = s["account"]
orderreq["secu_code"] = "601398"
orderreq["trd_id"] = "0B"
orderreq["price"] = "5.00"
orderreq["qty"] = "100"
orderreq.send()
orderresp = jz.SubmitOrderResp(s)
orderresp.recv()
s.storetrade(orderreq.payload, orderresp.payload)

orderreqjsyh = jz.SubmitOrderReq(s)
orderreqjsyh["user_code"] = s["user_code"]
orderreqjsyh["market"] = "10"
orderreqjsyh["secu_acc"] = s["secu_acc"]["sh"]
orderreqjsyh["account"] = s["account"]
orderreqjsyh["secu_code"] = "601939"
orderreqjsyh["trd_id"] = "0B"
orderreqjsyh["price"] = "5.70"
orderreqjsyh["qty"] = "100"
orderreqjsyh["biz_no"] = orderresp.records[0][1]
orderreqjsyh.send()
orderrespjsyh = jz.SubmitOrderResp(s)
orderrespjsyh.recv()
s.storetrade(orderreqjsyh.payload, orderrespjsyh.payload)

orderreqzgyh = jz.SubmitOrderReq(s)
orderreqzgyh["user_code"] = s["user_code"]
orderreqzgyh["market"] = "10"
orderreqzgyh["secu_acc"] = s["secu_acc"]["sh"]
orderreqzgyh["account"] = s["account"]
orderreqzgyh["secu_code"] = "601939"
orderreqzgyh["trd_id"] = "0B"
orderreqzgyh["price"] = "5.70"
orderreqzgyh["qty"] = "100"
orderreqzgyh["biz_no"] = orderresp.records[0][1]
orderreqzgyh.send()
orderrespzgyh = jz.SubmitOrderResp(s)
orderrespzgyh.recv()
s.storetrade(orderreqzgyh.payload, orderrespzgyh.payload)

# conn.close()
