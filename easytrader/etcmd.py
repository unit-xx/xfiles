import jz
import socket

# sign in system
jzserver = "172.18.20.52"
jzport = 9100

conn = socket.socket()
conn.connect((jzserver, jzport))

s = jz.session(conn)
cireq = jz.CheckinReq(s)
cireq.send()
ciresp = jz.CheckinResp(s)
ciresp.recv()
# update workkey
s["workkey"] = ciresp.getworkkey()

mktinforeq = jz.MarketinfoReq(s)
mktinforeq.send()
mktinforesp = jz.MarketinfoResp(s)
mktinforesp.recv()

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
s["usercode"] = loginresp.records[0][4]
s["branch"] = loginresp.records[0][6]
s["channel"] = "4"
s["session"] = loginresp.records[0][7]

usercode = s["usercode"]

cqreq = jz.CapitalQueryReq(s)
cqreq["usercode"] = usercode
#cqreq["currency"] = "0"
cqreq.send()
cqresp = jz.CapitalQueryResp(s)
cqresp.recv()



# conn.close()
