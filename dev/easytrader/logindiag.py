from login import Ui_logindlg
from PyQt4.QtGui import *
from PyQt4.QtCore import *


class logindlg(QDialog):
    def __init__(self, jzconfig, jsdconfig):
        QDialog.__init__(self)
        self.status = False
        self.ui = Ui_logindlg()
        self.ui.setupUi(self)
        self.jzconfig = jzconfig
        self.jsdconfig = jsdconfig

        # set data for lineedit controls
        self.ui.servaddr.setText(jzconfig["jzserver"])
        self.ui.servport.setText(str(jzconfig["jzport"]))
        self.ui.account.setText(jzconfig["jzaccount"])
        self.ui.passwd.setText(jzconfig["jzpasswd"])

        self.ui.servaddr_jsd.setText(jsdconfig["jsdserver"])
        self.ui.servport_jsd.setText(str(jsdconfig["jsdport"]))
        self.ui.account_jsd.setText(jsdconfig["jsdaccount"])
        self.ui.passwd_jsd.setText(jsdconfig["jsdpasswd"])

        self.connect(self.ui.ok, SIGNAL("clicked()"), self.on_ok)
        self.connect(self.ui.cancel, SIGNAL("clicked()"), self.on_cancel)

    def on_ok(self):
        self.done(1)
        self.status = True
        self.jzconfig["jzserver"] = str(self.ui.servaddr.text())
        self.jzconfig["jzport"] = int(self.ui.servport.text())
        self.jzconfig["jzaccount"] = str(self.ui.account.text())
        self.jzconfig["jzpasswd"] = str(self.ui.passwd.text())

        self.jsdconfig["jsdserver"] = str(self.ui.servaddr_jsd.text())
        self.jsdconfig["jsdport"] = int(self.ui.servport_jsd.text())
        self.jsdconfig["jsdaccount"] = str(self.ui.account_jsd.text())
        self.jsdconfig["jsdpasswd"] = str(self.ui.passwd_jsd.text())

    def on_cancel(self):
        self.status = False
        self.done(0)
