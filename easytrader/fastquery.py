import jz
import socket
import sys
from datetime import datetime
import time

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

while 1:
    qoreq = jz.QueryOrderReq(s)
    today = str(datetime.today().date())
    qoreq["begin_date"] = today
    qoreq["end_date"] = today
    qoreq["get_orders_mode"] = "0" # all submissions
    qoreq["user_code"] = s["user_code"]

    qoreq["biz_no"] = sys.argv[1]
    print qoreq.serialize()
    print s["workkey"]
    qoreq.send()

    qoresp = jz.QueryOrderResp(s)
    qoresp.recv()
    if qoresp.retcode != "0":
        print "failed", qoresp.retcode, qoresp.retinfo
        time.sleep(1)
    else:
        print "success", qoresp.retcode, qoresp.retinfo
    break
