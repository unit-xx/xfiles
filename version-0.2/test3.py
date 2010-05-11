import sys
import logindiag
from PyQt4.QtCore import *
from PyQt4.QtGui import *

config= {}
config["tradedbfn"] = "tradeinfo.db"
config["jzserver"] = "172.18.20.52"
config["jzport"] = 9100
config["jzaccount"] = "85804530"
config["jzaccounttype"] = "Z"
config["jzpasswd"] = "123444"

app = QApplication(sys.argv)

d = logindiag.logindlg(config)
d.show()
d.exec_()
