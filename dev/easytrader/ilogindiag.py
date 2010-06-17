from ilogin import Ui_logindlg
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
        self.ui.accountstock.setText(jzconfig["jzaccount"])
        self.ui.passwdstock.setText(jzconfig["jzpasswd"])

        self.ui.accountsindex.setText(jsdconfig["jsdaccount"])
        self.ui.passwdsindex.setText(jsdconfig["jsdpasswd"])

        self.connect(self.ui.ok, SIGNAL("clicked()"), self.on_ok)
        self.connect(self.ui.cancel, SIGNAL("clicked()"), self.on_cancel)

    def on_ok(self):
        self.done(1)
        self.status = True
        self.jzconfig["jzaccount"] = str(self.ui.accountstock.text())
        self.jzconfig["jzpasswd"] = str(self.ui.passwdstock.text())
        self.jsdconfig["jsdaccount"] = str(self.ui.accountsindex.text())
        self.jsdconfig["jsdpasswd"] = str(self.ui.passwdsindex.text())

    def on_cancel(self):
        self.status = False
        self.done(0)
