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

qoreq = jz.QueryOrderReq(s)
today = str(datetime.today().date())
qoreq["begin_date"] = today
qoreq["end_date"] = today
qoreq["get_orders_mode"] = "0" # all submissions
qoreq["user_code"] = s["user_code"]

#qoreq["order_id"] = "17063324"
# NOTE: use order_id in QueryOrderReq as biz_no in QueryOrder
qoreq["biz_no"] = "17063331"
#qoreq["account"] = s["account"]

#qoreq["market"] = "00"
#qoreq["secu_acc"] = s["secu_acc"]["SH"]
#qoreq["secu_code"] = "601398"
#orderreq["trd_id"] = "0B"

#qoreq["market"] = "10"
#qoreq["order_id"] = "17063323"
qoreq.send()
print qoreq.payload

qoresp = jz.QueryOrderResp(s)
qoresp.recv()
print qoresp.hasnext
print qoresp.sections
print qoresp.records
print qoresp.retcode
print qoresp.retinfo

