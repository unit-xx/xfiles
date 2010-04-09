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

dealreq = jz.DealReq(s)
today = str(datetime.today().date())
dealreq["begin_date"] = today
dealreq["end_date"] = today
dealreq["user_code"] = s["user_code"]

#dealreq["order_id"] = "17063324"
# NOTE: use order_id in QueryOrderReq as biz_no in QueryOrder
#dealreq["order_id"] = "17063327"
#dealreq["account"] = s["account"]

#dealreq["market"] = "00"
#dealreq["secu_acc"] = s["secu_acc"]["SH"]
#dealreq["secu_code"] = "601398"
#orderreq["trd_id"] = "0B"

#dealreq["market"] = "10"
#dealreq["order_id"] = "17063323"
dealreq.send()
print dealreq.payload

dealresp = jz.DealResp(s)
dealresp.recv()
print dealresp.hasnext
print dealresp.sections
print dealresp.records
print dealresp.retcode
print dealresp.retinfo

