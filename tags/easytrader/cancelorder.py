import jz
import socket
import sys
from datetime import datetime

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

mkt, order_id = sys.argv[1], sys.argv[2]
if mkt == "SH":
    mkt = "10"
elif mkt == "SZ":
    mkt = "00"
cancelorderreq = jz.CancelOrderReq(s)
cancelorderreq["market"] = mkt
cancelorderreq["order_id"] = order_id

cancelorderreq.send()
print cancelorderreq.payload

cancelorderresp = jz.CancelOrderResp(s)
cancelorderresp.recv()
print cancelorderresp.retcode
print cancelorderresp.retinfo
print cancelorderresp.hasnext
print cancelorderresp.sections
print cancelorderresp.records
