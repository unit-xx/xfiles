# -*- coding: utf-8 -*-

import sys
import os
import getpass
import socket
import pickle
import zlib
import Queue
import ConfigParser

from threading import Thread
import logging, logging.config
from struct import pack, unpack

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import jsd
from cparbiui import Ui_MainWindow

# 1 gui thread, the main thread
# 2 worker thread for long/short each stock index
# 1 update thread for monitor prices and diffs, and issue instructions
# 1 updater thread fro watching positons
# auotmatically, if set.

class Portfolio:
    def __init__(self, wqueue):
        self.attr = ["direction", "code", "share",
                "latest", "b1", "s1", "current",
                "pricepolicy",
                "position"]
        self.attrmap = {
                "direction":u"方向",
                "code":u"代码",
                "latest":u"最新价",
                "b1":u"买一",
                "s1":u"卖一",
                "share":u"操作单位",
                "position":u"持仓"
                }
        self.showattr = ["direction", "code", "share",
                "latest", "b1", "s1",
                "position"]

        self.pricepolicy = ["latest", "b1", "s1", "current"]
        self.pricepolicymap = {
                "latest":u"最新价",
                "b1":u"买一",
                "s1":u"卖一",
                "current":u"现价"
                }

        self.data = {}
        self.ptfn = ""

        self.autosubmit = False
        self.openpoint = 0.0
        self.closepoint = 0.0
        self.opentotal = 0
        self.trigger = 0
        self.wqueue = wqueue

    def load(self, config):
        MYSEC = "migrate"
        share = config.get(MYSEC, "share")

        self.data["long"] = {}
        self.data["long"]["direction"] = u"买入平仓"
        self.data["long"]["code"] = config.get(MYSEC, "close")
        self.data["long"]["share"] = share
        self.data["long"]["pricepolicy"] = "current"
        self.data["long"]["current"] = "0.0"

        self.data["short"] = {}
        self.data["short"]["direction"] = u"卖出开仓"
        self.data["short"]["code"] = config.get(MYSEC, "open")
        self.data["short"]["share"] = share
        self.data["short"]["pricepolicy"] = "current"
        self.data["short"]["current"] = "0.0"

        self.openpoint = config.getfloat(MYSEC, "openpoint")
        self.closepoint = config.getfloat(MYSEC, "closepoint")
        self.opentotal = config.getint(MYSEC, "opentotal")
        self.trigger = config.getint(MYSEC, "trigger")

    def domigrate(self):
        self.wqueue.put((
            "close",
            "short",
            self.data["long"]["code"],
            "0.0",
            self.data["long"]["share"]))

        self.wqueue.put((
            "open",
            "short",
            self.data["short"]["code"],
            "0.0",
            self.data["short"]["share"]))

    def doclose(self):
        return

class CPArbiModel(QAbstractTableModel):
    def __init__(self, portfolio, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.portfolio = portfolio

    def rowCount(self, parent):
        return len(self.portfolio.data)

    def columnCount(self, parent):
        return len(self.portfolio.attrmap)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            hname = self.portfolio.showattr[section]
            try:
                hname = self.portfolio.attrmap[hname]
            except KeyError:
                pass
            return QVariant(hname)
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return QVariant(str(section + 1))
        return QVariant()

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        columnkey = self.portfolio.showattr[index.column()]
        if index.row() == 0:
            rowkey = "long"
        else:
            rowkey = "short"
        try:
            rawdata = self.portfolio.data[rowkey][columnkey]
            if not isinstance(rawdata, unicode):
                # expect rawdata as numbers here
                rawdata = str(rawdata)
            celldata = QString(rawdata)
            return QVariant(celldata)
        except KeyError:
            return QVariant()

    @pyqtSlot()
    def updaterow(self):
        self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                self.index(0,0),
                self.index(1, len(self.portfolio.showattr)-1))

class cparbigui(QMainWindow, Ui_MainWindow):
    def __init__(self, portfolio):
        QMainWindow.__init__(self)
        self.portfolio = portfolio

    def setup(self, model):
        self.setupUi(self)
        self.setWindowTitle(u"移仓")
        self.arbitbl.setModel(model)
        self.autochk.setChecked(self.portfolio.autosubmit)
        self.openspin.setValue(self.portfolio.openpoint)
        self.closespin.setValue(self.portfolio.closepoint)
        self.opentimespin.setValue(self.portfolio.opentotal)
        self.triggercountspin.setValue(self.portfolio.trigger)

    @pyqtSlot()
    def on_openbtn_clicked(self):
        self.portfolio.domigrate()

    @pyqtSlot()
    def on_closebtn_clicked(self):
        self.portfolio.doclose()

    @pyqtSlot(int)
    def on_autochk_stateChanged(self, state):
        self.portfolio.autosubmit = self.autochk.isChecked()
        if self.portfolio.autosubmit == True:
            self.autogrp.setEnabled(False)
            self.openbtn.setEnabled(False)
            self.closebtn.setEnabled(False)

            self.portfolio.openpoint = self.openspin.value()
            self.portfolio.closepoint = self.closespin.value()
            self.portfolio.opentotal = self.opentimespin.value()
            self.portfolio.trigger = self.triggercountspin.value()

        elif self.portfolio.autosubmit == False:
            self.autogrp.setEnabled(True)
            self.openbtn.setEnabled(True)
            self.closebtn.setEnabled(True)

class monitor(Thread):
    def __init__(self, ui, portfolio, model, hqserver):
        Thread.__init__(self)
        self.ui = ui
        self.portfolio = portfolio
        self.model = model
        self.hqserver = hqserver
        self.conn = None
        self.runflag = True
        self.logger = logging.getLogger()

        self.opentriggercount = 0
        self.closetriggercount = 0
        self.opencount = 0
        self.closecount = 0

    def stop(self):
        self.runflag = False

    def updateprice(self, quotaData):
        for qd in quotaData:
            data = self.portfolio.data
            item = None
            qdcode = qd.varity_code+qd.deliv_date
            if qdcode == data["short"]["code"]:
                item = data["short"]
            elif qdcode == data["long"]["code"]:
                item = data["long"]

            if item:
                item["latest"] = "%0.1f" % qd.lastPrice
                item["b1"] = "%0.1f" % qd.bidPrice1
                item["s1"] = "%0.1f" % qd.askPrice1
                QMetaObject.invokeMethod(self.model,
                        "updaterow", Qt.QueuedConnection)

    def update(self):
        (pktlen,) = unpack("!I", self.conn.recv(4))
        left = pktlen
        content = []
        while 1:
            if left <= 0:
                break
            buf = self.conn.recv(left)
            content.append(buf)
            left = left - len(buf)

        data = "".join(content)
        data = pickle.loads(zlib.decompress(data))

        self.updateprice(data)

        openpricediff = 0.0
        closepricediff = 0.0
        try:
            openpricediff = (float(self.portfolio.data["long"]["s1"]) 
                            - float(self.portfolio.data["short"]["b1"]))
            closepricediff = (float(self.portfolio.data["long"]["b1"]) 
                            - float(self.portfolio.data["short"]["s1"]))
        except KeyError:
            pass

        QMetaObject.invokeMethod(self.ui.openbasediffline,
                "setText",
                Q_ARG("QString",
                    QString("%0.1f"%openpricediff)))

        QMetaObject.invokeMethod(self.ui.closebasediffline,
                "setText",
                Q_ARG("QString",
                    QString("%0.1f"%closepricediff)))

        if self.portfolio.autosubmit:
            if openpricediff <= self.portfolio.openpoint:
                self.opentriggercount += 1
                if self.opentriggercount >= self.portfolio.trigger and self.opencount < self.portfolio.opentotal:
                    self.portfolio.doopen()
                    self.logger.info("open@%0.1f" % openpricediff)
                    self.opencount += 1
            else:
                self.opentriggercount = 0

            if closepricediff >= self.portfolio.closepoint:
                self.closetriggercount += 1
                if self.closetriggercount >= self.portfolio.trigger and self.closecount < self.opencount:
                    self.portfolio.doclose()
                    self.logger.info("close@%0.1f" % closepricediff)
                    self.closecount += 1
            else:
                self.closetriggercount = 0

    def run(self):
        try:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.connect(self.hqserver)
        except socket.error:
            print "cannot connect hq"
            return

        try:
            self.update()
            self.ui.arbitbl.resizeColumnsToContents()
            while self.runflag:
                self.update()
        except Exception:
            self.logger.exception("Oh!!!")
        finally:
            self.conn.close()

class worker(Thread):
    def __init__(self, wqueue, jsdcfg):
        Thread.__init__(self)
        self.wqueue = wqueue
        self.jsdcfg = jsdcfg
        self.jsd = None
        self.runflag = True

    def stop(self):
        self.runflag = False

    def setup(self):
        self.jsd = jsd.session(self.jsdcfg)
        if not self.jsd.setup():
            self.jsd.close()
            print "cannot login into jsd."
            return False
        return True

    def run(self):
        if self.setup():
            while self.runflag:
                try:
                    (
                            openclose,
                            longshort,
                            code,
                            price,
                            share)  = self.wqueue.get(True, 1)
                    self.wqueue.task_done()

                    req = jsd.OrderReq(self.jsd)
                    resp = jsd.OrderResp(self.jsd)
                    if openclose == "open":
                        if longshort == "long":
                            req.makeopenlong(code, price, share)
                        elif longshort == "short":
                            req.makeopenshort(code, price, share)
                    elif openclose == "close":
                        if longshort == "long":
                            req.makecloselong(code, price, share)
                        elif longshort == "short":
                            req.makecloseshort(code, price, share)

                    req.send()
                    resp.recv()
                    print resp.records
                    print
                except Queue.Empty:
                    pass

def main(args):
    app = QApplication(args)
    os.chdir(os.path.dirname(os.path.abspath(args[0])))
    try:
        CONFIGFN = sys.argv[1]
    except IndexError:
        print "Usage: %s <migrate-spec>" % args[0]
        sys.exit(1)

    logging.config.fileConfig(CONFIGFN)
    logger = logging.getLogger()
    msg = "i'm started"
    logger.info("========================")
    logger.info(msg)

    config = ConfigParser.ConfigParser()
    config.read(CONFIGFN)
    jsdcfg = {}
    for k,v in config.items("jsd"):
        jsdcfg[k] = v
    try:
        jsdcfg["jsdport"] = int(jsdcfg["jsdport"])
    except KeyError:
        jsdcfg["jsdport"] = 9100
    jsdcfg["jsdpasswd"] = getpass.getpass("Password: ")

    wqueue = Queue.Queue()
    p = Portfolio(wqueue)
    p.load(config)

    arbimodel = CPArbiModel(p)

    ui = cparbigui(p)
    ui.setup(arbimodel)
    ui.show()

    hqaddr = config.get("jsd", "hqaddr")
    hqport = config.getint("jsd", "hqport")
    m = monitor(ui, p, arbimodel, (hqaddr, hqport))
    m.start()

    w1 = worker(wqueue, jsdcfg)
    w2 = worker(wqueue, jsdcfg)
    w1.start()
    w2.start()

    app.exec_()

    w2.stop()
    w1.stop()
    w2.join()
    w1.join()

    m.stop()
    m.join()

if __name__=="__main__":
    main(sys.argv)
