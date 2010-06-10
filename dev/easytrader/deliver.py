# -*- coding: utf-8 -*-

import os
import sys
import time
import datetime
from threading import Thread

from dbfpy import dbf
from PyQt4.QtGui import *
from PyQt4.QtCore import *

import jsd
from deliverdlg import Ui_deliverdlg

START = datetime.time(13, 00, 00)
END = datetime.time(15, 00, 00)
dbfn = "z:\\show2003.dbf"
hs300code = "000300"

class deliverdlg(QDialog, Ui_deliverdlg):
    def __init__(self, jsdcfg):
        QDialog.__init__(self)
        self.jsdcfg = jsdcfg

    def setup(self):
        self.setupUi(self)

        #s = jsd.session(jsdcfg)
        #if not s.setup():
        #    pass

    @pyqtSlot()
    def fullcombo(self):
        self.sindexcmb.addItem(u"你好啊")

class updater(Thread):
    def __init__(self, ui):
        Thread.__init__(self)
        self.ui = ui

    def run(self):
        #QMetaObject.invokeMethod(self.ui.sindexcmb, "addItem",
        #        Qt.QueuedConnection,
        #        Q_ARG("QString", QString(u"你好啊")))

        QMetaObject.invokeMethod(self.ui, "fullcombo",
                Qt.QueuedConnection)

        #self.ui.sindexcmb.addItem(u"你好啊")

def main(args):
    app = QApplication(args)
    now = datetime.datetime.now().time()
    dbsh = dbf.Dbf(dbfn, ignoreErrors=True, readOnly=True)
    i = 0
    hs300index = -1
    for rec in dbsh:
        if rec["S1"] == hs300code:
            hs300index = i
            break
        i = i + 1
    assert hs300index != -1

    jsdcfg = {}
    ddlg = deliverdlg(jsdcfg)
    ddlg.setup()

    updater(ddlg).start()

    ddlg.show()
    app.exec_()

    if now < START:
        ddlg.statusline.setText("等待开始计算（%s）", str(START))
        print "waiting to start at", START

        while 1:
            time.sleep(1)
            now = datetime.datetime.now().time()
            if now >= START:
                break

    avg = 0
    n = 0
    print "start calculating delivery price."
    while 1:
        a = dbsh[hs300index]["S8"]
        avg = avg * n / (n+1) + a / (n+1)
        n = n + 1
        print "%0.3f" % avg
        time.sleep(5)
        now = datetime.datetime.now().time()
        if now > END:
            break

if __name__=="__main__":
    main(sys.argv)
