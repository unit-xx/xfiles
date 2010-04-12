import jz
import socket
import sys
from datetime import datetime

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

f = open(sys.argv[1])
for line in f:
    mkt, order_id = line.split()
    cancelorderreq = jz.CancelOrderReq(s)
    cancelorderreq["market"] = mkt
    cancelorderreq["order_id"] = order_id

    cancelorderreq.send()
    print cancelorderreq.payload

    cancelorderresp = jz.CancelOrderResp(s)
    cancelorderresp.recv()
    print cancelorderresp.hasnext
    print cancelorderresp.sections
    print cancelorderresp.records
    print cancelorderresp.retcode
    print cancelorderresp.retinfo


