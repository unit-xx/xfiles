import jz
import socket
import sys

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
else:
    print "Cannot login"
    sys.exit(1)

qoreq = jz.QueryOrderReq(s)
qoreq["user_code"] = s["user_code"]
qoreq["market"] = "10"
qoreq["order_id"] = "17063320"
qoreq.send()
print qoreq.payload
qoresp = jz.QueryOrderResp(s)
qoresp.recv()

