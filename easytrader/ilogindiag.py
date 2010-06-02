from ilogin import Ui_logindlg
from PyQt4.QtGui import *
from PyQt4.QtCore import *


class logindlg(QDialog):
    def __init__(self, config):
        QDialog.__init__(self)
        self.status = False
        self.ui = Ui_logindlg()
        self.ui.setupUi(self)
        self.config = config

        # set data for lineedit controls
        self.ui.account.setText(config["jzaccount"])
        self.ui.passwd.setText(config["jzpasswd"])

        self.connect(self.ui.ok, SIGNAL("clicked()"), self.on_ok)
        self.connect(self.ui.cancel, SIGNAL("clicked()"), self.on_cancel)

    def on_ok(self):
        self.done(1)
        self.status = True
        self.config["jzaccount"] = str(self.ui.account.text())
        self.config["jzpasswd"] = str(self.ui.passwd.text())

    def on_cancel(self):
        self.status = False
        self.done(0)
