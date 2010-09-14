import jz
import socket
import sys
from datetime import datetime

# config
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

qoreq = jz.QueryOrderReq(s)
today = str(datetime.today().date())
qoreq["begin_date"] = today
qoreq["end_date"] = today
qoreq["get_orders_mode"] = "0" # all submissions
qoreq["user_code"] = s["user_code"]
print s["user_code"]

try:
    qoreq["biz_no"] = sys.argv[1]
except IndexError:
    pass
# NOTE: use order_id in QueryOrderReq as biz_no in QueryOrder
#qoreq["biz_no"] = "17063331"
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
print qoresp.header_left
print qoresp.sections
print qoresp.records
orders = []
for r in qoresp.records:
    if r[15] == r[-11]:
        print r
        orders.append(r[10])
        print
print qoresp.hasnext
print qoresp.retcode
print qoresp.retinfo
print orders
