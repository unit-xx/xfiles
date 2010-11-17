import jz
import socket
import sys
from datetime import datetime

# config
session_config = {}
session_config["tradedbfn"] = "tradeinfo.db"
session_config["jzserver"] = "172.18.12.205"
session_config["jzport"] = 9100
session_config["jzaccount"] = ""
session_config["jzaccounttype"] = "Z"
session_config["jzpasswd"] = ""

s = jz.session(session_config)
if not s.setup():
    print "Cannot login"
    sys.exit(1)

sireq = jz.SecuInfoReq(s)
sireq["market"] = jz.SZAMARKET
sireq["secu_code"] = "000012"
sireq.send()
siresp = jz.SecuInfoResp(s)
siresp.recv()
print siresp.records

