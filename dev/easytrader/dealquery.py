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

dealreq = jz.DealReq(s)
today = str(datetime.today().date())
dealreq["begin_date"] = today
dealreq["end_date"] = today
dealreq["user_code"] = s["user_code"]
dealreq["order_id"] = sys.argv[1]

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
print dealresp.sections
print dealresp.records
print dealresp.hasnext
print dealresp.retcode
print dealresp.retinfo

