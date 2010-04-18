# -*- coding: utf-8 -*-

import sys
import socket
import pickle
from queue import Queue
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from tradeui import Ui_MainWindow
from dbfpy import dbf
from threading import Thread
import time
import shutil
import types
import jz
from datetime import datetime

class PortfolioModel(QAbstractTableModel):
    def __init__(self, portfolio, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.portfolio = portfolio

    def rowCount(self, parent):
        return len(self.portfolio.stocklist)

    def columnCount(self, parent):
        return len(self.portfolio.stockmodelattr)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.portfolio.stockmodelattr[section])
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return QVariant(str(section + 1))
        return QVariant()

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        rowkey = self.portfolio.stocklist[index.row()]
        columnkey = self.portfolio.stockmodelattr[index.column()]
        try:
            celldata = self.portfolio.stockinfo[rowkey][columnkey]
            return QVariant(celldata)
        except KeyError:
            return QVariant()

class Portfolio:
#    def __init__(self, stocklist, stockcount):
#        # list is stock id
#        self.stocklist = stocklist
#        self.stockattr = ["count", "code", "name", "latest", "buy", "sell"]
#        self.stockset = set(stocklist)
#        self.stockcount = stockcount
#        self.data = {}
#        for i in range(len(self.stocklist)):
#            s = self.stocklist[i]
#            self.data.setdefault(s, {})
#            self.data[s]["code"] = s
#            self.data[s]["count"] = self.stockcount[i]

    # stock states can be:
    UNORDERED = "UNORDERED"
    ORDERFAILED = "ORDERFAILED"
    ORDERSUCCESS = "ORDERSUCCESS"
    # assumption: only success order can be canceled
    CANCELSUCCESS = "CANCELSUCCESS"
    CANCELFAILED = "CANCELFAILED"


    def __init__(self, stockbatch, sessioncfg, tqueue):
        # market code (SH, SZ), stock number, count
        self.session = jz.session(sessioncfg)
        if not self.session.setup():
            print "session setup failed."
            sys.exit(1)
        self.tqueue = tqueue

        self.stocklist = []
        self.stockset = set()
        self.stockattr = ["count", "market", "code", "name", "latestprice",
                "buyprice", "sellprice", "order_id", "order_date", "order_time",
                "orderedcount", "orderprice", "dealcount", "dealprice", "order_state",
                "cancel_date", "cancel_time"]
        self.stockmodelattr = ["count", "market", "code", "name", "order_state",
                "order_date", "order_time", "orderedcount", "dealcount", "orderprice",
                "dealprice", "latestprice"]
        # TODO: really need this assertion? how about derived attr
        assert(set(self.stockmodelattr) <= set(self.stockattr))
        self.pricepolicylist = ["latest", "b1", "b2", "b3", "b4", "b5",
                "s1", "s2", "s3", "s4", "s5"]
        self.pricepolicy = "s5"
        # use market+stock number as key
        self.dealrecord = {}
        self.stockinfo = {}
        for i in stockbatch:
            scode = i[0].upper() + i[1]
            self.stocklist.append(scode)
            self.stockinfo.setdefault(scode, {})
            self.dealrecord.setdefault(scode, {})

            self.stockinfo[scode]["market"] = i[0].upper()
            self.stockinfo[scode]["code"] = i[1]
            self.stockinfo[scode]["count"] = i[2]
            self.stockinfo[scode]["order_state"] = Portfolio.UNORDERED
            self.stockinfo[scode]["order_id"] = ""
            self.stockinfo[scode]["order_date"] = ""
            self.stockinfo[scode]["order_time"] = ""
            try:
                self.stockinfo[scode]["order_state"] = i[3]
                self.stockinfo[scode]["order_id"] = i[4]
                self.stockinfo[scode]["order_date"] = i[5]
                self.stockinfo[scode]["order_time"] = i[6]
            except IndexError:
                pass
        self.stockset = set(self.stocklist)

    def __del__(self):
        self.session.close()

    @staticmethod
    def readBatchOrder(bofn):
        # bofn specifies batch order in lines, each lines contains
        # market code (SH, SZ), stock code, count and order_id, order_state, order_date, order_time
        # separated by spaces
        # return: batch orders in a list, and bad lines
        bo = []
        badlines = []
        f = open(bofn)
        for line in f:
            if line == "": # EOF
                break

            boitem = line.split()
            if len(boitem) < 3: # empty line or others
                if line != "\n":
                    badlines.append(line.strip())
                continue

            if( (boitem[0].upper()!="SH" and boitem[0].upper()!="SZ") or (int(boitem[2])%100 != 0) ):
                badlines.append(line.strip())
                continue

            bo.append(boitem)
        f.close()
        return (bo, badlines)

    def saveBatchOrder(self, bofn):
        # TODO: save ordered? canceled? failed?
        f = open(bofn, "w")
        for scode in self.stocklist:
            si = self.stockinfo[scode]
            f.write(" ".join( (si["market"], si["code"], si["count"], si["order_state"],
                si["order_id"], si["order_date"], si["order_time"]) ))
            f.write("\n")
        f.flush()
        f.close()

    def submitBatchOrderSync(self, trdid):
        # return:

        # submit first order item, use its order_id as following orders' biz_no
        if len(self.stocklist) == 0:
            return

        trdid == ""
        if trdid == "buy":
            trdcode = "0B"
        elif trdid == "sell":
            trdcode = "0S"
        assert(trdcode != "")

        today = str(datetime.today().date())
        for scode in self.stocklist:
            if self.stockinfo[scode]["order_state"] == Portfolio.UNORDERED:
                req = jz.SubmitOrderReq(self.session)
                req["user_code"] = self.session["user_code"]
                if self.stockinfo[scode]["market"] == "SH":
                    req["market"] = "10"
                    req["secu_acc"] = self.session["secu_acc"]["SH"]
                elif self.stockinfo[scode]["market"] == "SZ":
                    req["market"] = "00"
                    req["secu_acc"] = self.session["secu_acc"]["SZ"]
                req["account"] = self.session["account"]
                req["secu_code"] = self.stockinfo[scode]["code"]
                req["trd_id"] = trdcode
                req["price"] = self.stockinfo[scode]["orderprice"]
                req["qty"] = self.stockinfo[scode]["count"]
                #if first_order_id != "":
                #    req["biz_no"] = first_order_id
                req.send()
                resp = jz.SubmitOrderResp(self.session)
                resp.recv()
                self.session.storetrade(req, resp)
                if resp.retcode == "0":
                    self.stockinfo[scode]["order_id"] = resp.records[0][1]
                    self.stockinfo[scode]["order_date"] = today
                    self.stockinfo[scode]["order_time"] = str(datetime.now().time())
                    self.stockinfo[scode]["order_state"] = Portfolio.ORDERSUCCESS
                else:
                    self.stockinfo[scode]["order_state"] = Portfolio.ORDERFAILED


    submitBatchOrder = submitBatchOrderSync

    def submitBatchOrderTop(self, trdid):
        if len(self.stocklist) == 0:
            return

        trdid == ""
        if trdid == "buy":
            trdcode = "0B"
        elif trdid == "sell":
            trdcode = "0S"
        assert(trdcode != "")

        reqclass = jz.SubmitOrderReq
        respclass = jz.SubmitOrderResp
        for scode in self.stocklist:
            if self.stockinfo[scode]["order_state"] == Portfolio.UNORDERED:
                param = {}
                param["user_code"] = self.session["user_code"]
                if self.stockinfo[scode]["market"] == "SH":
                    param["market"] = "10"
                    param["secu_acc"] = self.session["secu_acc"]["SH"]
                elif self.stockinfo[scode]["market"] == "SZ":
                    param["market"] = "00"
                    param["secu_acc"] = self.session["secu_acc"]["SZ"]
                param["account"] = self.session["account"]
                param["secu_code"] = self.stockinfo[scode]["code"]
                param["trd_id"] = trdcode
                param["price"] = self.stockinfo[scode]["orderprice"]
                param["qty"] = self.stockinfo[scode]["count"]
                self.tqueue.put( (reqclass, respclass, param, self.submitBatchOrderBottom) )

    def submitBatchOrderBottom(self, req, resp, param):
        today = str(datetime.today().date())
        self.session.storetrade(req, resp)
        mkt = ""
        if param["market"] == "10":
            mkt = "SH"
        elif param["market"] == "00":
            mkt = "SZ"
        assert mkt != ""
        scode = mkt + param["secu_code"]
        if resp.retcode == "0":
            self.stockinfo[scode]["order_id"] = resp.records[0][1]
            self.stockinfo[scode]["order_date"] = today
            self.stockinfo[scode]["order_time"] = str(datetime.now().time())
            self.stockinfo[scode]["order_state"] = Portfolio.ORDERSUCCESS
        else:
            self.stockinfo[scode]["order_state"] = Portfolio.ORDERFAILED

    def cancelBatchOrder(self):
        # only success orders can be canceled
        today = str(datetime.today().date())
        for scode in self.stocklist:
            if self.stockinfo[scode]["order_state"] == Portfolio.ORDERSUCCESS:
                req = jz.CancelOrderReq(self.session)
                req["user_code"] = self.session["user_code"]
                if self.stockinfo[scode]["market"] == "SH":
                    req["market"] = "10"
                elif self.stockinfo[scode]["market"] == "SZ":
                    req["market"] = "00"
                req["order_id"] = self.stockinfo[scode]["order_id"]
                req.send()
                resp = jz.CancelOrderResp(self.session)
                resp.recv()
                self.session.storetrade(req, resp)
                if resp.retcode == "0":
                    self.stockinfo[scode]["order_state"] = Portfolio.CANCELSUCCESS
                    self.stockinfo[scode]["cancel_date"] = today
                    self.stockinfo[scode]["cancel_time"] = str(datetime.now().time())
                else:
                    self.stockinfo[scode]["order_state"] = Portfolio.CANCELFAILED

    def genBackupOrder(self):
        # now only consider CANCELSUCCESS orders
        self.backuporder = {}
        self.backuporderlist = []
        backuporder = self.backuporder
        backuporderlist = self.backuporderlist
        for scode in self.stocklist:
            if self.stockinfo[scode]["order_state"] == Portfolio.CANCELSUCCESS:
            # TODO: round to 100
            # TODO: track non-dealed stock numbers, not only round and ignore
                backupcount = int(self.stockinfo[scode]["count"]) - int(self.stockinfo[scode]["dealcount"])
                if backupcount > 0:
                    backuporderlist.append(scode)
                    backuporder.setdefault(scode, {})
                    backuporder[scode]["market"] = self.stockinfo[scode]["market"]
                    backuporder[scode]["code"] = self.stockinfo[scode]["code"]
                    backuporder[scode]["count"] = str(backupcount)

    def saveBackupOrder(self, backupfn):
        f = open(backupfn, "w")
        for scode in self.backuporderlist:
            si = self.backuporder[scode]
            f.write(" ".join( (si["market"], si["code"], si["count"]) ))
            f.write("\n")
        f.flush()
        f.close()

    def genandsaveBackupOrder(self):
        fn = unicode(QFileDialog.getSaveFileName())
        self.genBackupOrder()
        self.saveBackupOrder(fn)

    def buybatch(self):
        self.submitBatchOrder("buy")

    def pricelatest(self):
        self.pricepolicy = "latest"

    def priceb1(self):
        self.pricepolicy = "b1"

    def priceb2(self):
        self.pricepolicy = "b2"

    def priceb3(self):
        self.pricepolicy = "b3"

    def priceb4(self):
        self.pricepolicy = "b4"

    def priceb5(self):
        self.pricepolicy = "b5"

    def prices1(self):
        self.pricepolicy = "s1"

    def prices2(self):
        self.pricepolicy = "s2"

    def prices3(self):
        self.pricepolicy = "s3"

    def prices4(self):
        self.pricepolicy = "s4"

    def prices5(self):
        self.pricepolicy = "s5"

class PortfolioUpdater(Thread):
    def __init__(self, shdbfn, shmapfn, szdbfn, szmapfn, portfolio, portmodel):
        Thread.__init__(self)
        self.shdbfn = shdbfn
        self.shmapfn = shmapfn
        self.szdbfn = szdbfn
        self.szmapfn = szmapfn
        self.dbsh = dbf.Dbf(self.shdbfn, ignoreErrors=True, readOnly=True)
        self.dbsz = dbf.Dbf(self.szdbfn, ignoreErrors=True, readOnly=True)
        f = open(self.shmapfn)
        self.shmap = pickle.load(f)
        f.close()
        f = open(self.szmapfn)
        self.szmap = pickle.load(f)
        f.close()
        self.portfolio = portfolio
        self.portmodel = portmodel
        self.runflag = True

        # one-to-one mapping of dbfield to stockattr, for SH
        self.shdbfield = ["S1", "S2", "S8", "S9", "S10"]
        self.shdbmapping = {
                "S1":"code",
                "S2":"name",
                "S8":"latestprice",
                "S9":"buyprice",
                "S10":"sellprice"
                }
        assert(len(self.shdbfield) == len(self.shdbmapping))

        # for SZ
        self.szdbfield = ["HQZQDM", "HQZQJC", "HQZJCJ", "HQBJW1", "HQSJW1"]
        self.szdbmapping = {
                "HQZQDM":"code",
                "HQZQJC":"name",
                "HQZJCJ":"latestprice",
                "HQBJW1":"buyprice",
                "HQSJW1":"sellprice"
                }
        assert(len(self.szdbfield) == len(self.szdbmapping))

    def __del__(self):
        self.dbsh.close()
        self.dbsz.close()

    def getpricesh(self, shrec, pricepolicy):
        price = ""
        policymapping = {
                "latest":"S8",
                "b1":"S9",
                "b2":"S16",
                "b3":"S18",
                "b4":"S26",
                "b5":"S28",
                "s1":"S10",
                "s2":"S22",
                "s3":"S24",
                "s4":"S30",
                "s5":"S32"
                }
        price = str(shrec[policymapping[pricepolicy]])
        assert(price != "")
        return price

    def getpricesz(self, szrec, pricepolicy):
        price = ""
        policymapping = {
                "latest":"HQZJCJ",
                "b1":"HQBJW1",
                "b2":"HQBJW2",
                "b3":"HQBJW3",
                "b4":"HQBJW4",
                "b5":"HQBJW5",
                "s1":"HQSJW1",
                "s2":"HQSJW2",
                "s3":"HQSJW3",
                "s4":"HQSJW4",
                "s5":"HQSJW5"
                }
        price = str(szrec[policymapping[pricepolicy]])
        assert(price != "")
        return price

    def update(self):
        # show2003 only considers SH market
        dbsh = self.dbsh
        dbsz = self.dbsz
        shmap = self.shmap
        szmap = self.szmap

        for scode = self.portfolio.stocklist:
            stockinfo = self.portfolio.stockinfo[scode]
            if stockinfo["market"] == "SH":
                rec = dbsh[shmap[scode]]
                for f in self.shdbfield:
                    if type(rec[f]) is types.StringType:
                        stockinfo[self.shdbmapping[f]] = rec[f].decode("GBK")
                    else:
                        stockinfo[self.shdbmapping[f]] = rec[f]
                stockinfo["orderprice"] = self.getpricesh(rec, self.portfolio.pricepolicy)
            elif stockinfo["market"] == "SZ":
                rec = dbsz[szmap[scode]]
                for f in self.szdbfield:
                    if type(rec[f]) is types.StringType:
                        stockinfo[self.szdbmapping[f]] = rec[f].decode("GBK")
                    else:
                        stockinfo[self.szdbmapping[f]] = rec[f]
                stockinfo["orderprice"] = self.getpricesz(rec, self.portfolio.pricepolicy)

        # update SH stock
        #for s in dbsh:
        #    # a dirty patch
        #    scode = "SH" + s[0]
        #    if scode in self.portfolio.stockset:
        #        stockinfo = self.portfolio.stockinfo[scode]
        #        for f in self.shdbfield:
        #            if type(s[f]) is types.StringType:
        #                stockinfo[self.shdbmapping[f]] = s[f].decode("GBK")
        #            else:
        #                stockinfo[self.shdbmapping[f]] = s[f]
        #        # update order price for SH
        #        stockinfo["orderprice"] = self.getpricesh(s, self.portfolio.pricepolicy)

        # update SZ stock
        #for s in dbsz:
        #    # a dirty patch
        #    scode = "SZ" + s[0]
        #    if scode in self.portfolio.stockset:
        #        stockinfo = self.portfolio.stockinfo[scode]
        #        for f in self.szdbfield:
        #            if type(s[f]) is types.StringType:
        #                stockinfo[self.szdbmapping[f]] = s[f].decode("GBK")
        #            else:
        #                stockinfo[self.szdbmapping[f]] = s[f]
        #        # update order price for SZ
        #        stockinfo["orderprice"] = self.getpricesz(s, self.portfolio.pricepolicy)

        self.portmodel.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                self.portmodel.index(0,0), self.portmodel.index(
                    len(self.portfolio.stockinfo)-1,
                    len(self.portfolio.stockmodelattr)-1))

    def stop(self):
        self.runflag = False

    def run(self):
        while self.runflag:
            self.update()
            #for d in self.portfolio.data:
            #    for field in self.dbfield:
            #        print self.portfolio.data[d][self.dbmapping[field]],
            #    print
            time.sleep(1)

class OrderUpdater(Thread):
    def __init__(self, portfolio, portmodel, sessioncfg):
        Thread.__init__(self)
        self.portfolio = portfolio
        self.portmodel = portmodel
        self.runflag = True
        self.session = jz.session(sessioncfg)
        if not self.session.setup():
            print "Session setup failed."
            sys.exit(1)

    def __del__(self):
        self.session.close()

    def update(self):
        for scode in self.portfolio.stocklist:
            si = self.portfolio.stockinfo[scode]
            if si["order_id"] != "":
                qoreq = jz.QueryOrderReq(self.session)
                qoreq["begin_date"] = si["order_date"]
                qoreq["end_date"] = si["order_date"]
                qoreq["get_orders_mode"] = "0" # all submissions
                qoreq["user_code"] = self.session["user_code"]
                # a bug in protocol/document results in next odd line
                qoreq["biz_no"] = si["order_id"]
                qoreq.send()
                qoresp = jz.QueryOrderResp(self.session)
                qoresp.recv()
                if qoresp.retcode == "0":
                    si["dealcount"] = qoresp.records[0][-11]
                    try:
                        si["dealprice"] = str( float(qoresp.records[0][-9]) / float(qoresp.records[0][-11]) )
                    except ZeroDivisionError:
                        si["dealprice"] = "0.00"
                    # TODO: ordercount may diff with count?
                    si["orderedcount"] = qoresp.records[0][15]
                else:
                    print "error when query order for %s" % si["order_id"]
                    print qoresp.retcode, qoresp.retinfo

    def stop(self):
        self.runflag = False

    def run(self):
        while self.runflag:
            self.update()
            #for d in self.portfolio.data:
            #    for field in self.dbfield:
            #        print self.portfolio.data[d][self.dbmapping[field]],
            #    print
            time.sleep(2)

class jzWorker(Thread):
    def __init__(self, session, tqueue):
        Thread.__init__(self)
        self.session = session
        self.tqueue = tqueue
        self.runflag = True

    def run(self):
        # TODO: what if et is closed while tqueue is not empty
        while self.runflag:
            t = tqueue.get()
            self.dotask(t)
            tqueue.task_done()

    def dotask(self, t):
        """
        t is a task as a tuple:
        (request class, response class, param, callback)

        callback will receive (req instance, resp instance, param)
        as its input parameters
        """
        req = t[0](self.session)
        param = t[2]
        callback = t[3]
        for k in param:
            req[k] = param[k]
        req.send()
        resp = t[1](self.session)
        resp.recv()
        callback(req, resp, param)

    def stop(self):
        self.runflag = False

def openfile():
    fn = QFileDialog.getOpenFileName()
    return fn

def testslot(t):
    print t

def verifymap(dbfn, mapfn, codekey):
    db = dbf.Dbf(dbfn, ignoreErrors=True, readOnly=True)
    f = open(mapfn)
    map = pickle.load(f)
    ret = True
    for k in map:
        if k != db[map[k]][codekey]:
            ret = False
            break
    f.close()
    db.close()
    return ret

def main(args):
    app = QApplication(args)
    window = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(window)

    # read config
    shdbfn = "z:\\show2003.dbf"
    szdbfn = "z:\\sjshq.dbf"
    shmapfn = "shmap.pkl"
    szmapfn = "szmap.pkl"
    if not verifymap(shdbfn, shmapfn, "S1"):
        print "Stock map file error."
    if not verifymap(szdbfn, szmapfn, "HQZQDM")
        print "Stock map file error."
    #portfoliofn = "hs300.txt"
    portfoliofn = openfile()

    session_config = {}
    session_config["tradedbfn"] = "tradeinfo.db"
    session_config["jzserver"] = "172.18.20.52"
    session_config["jzport"] = 9100
    session_config["jzaccount"] = "85804530"
    session_config["jzaccounttype"] = "Z"
    session_config["jzpasswd"] = "123444"

    # setup portfolio
    bo, badlines = Portfolio.readBatchOrder(portfoliofn)
    if len(badlines) > 0:
        print "There're bad lines."
        print badlines
    tqueue = Queue()
    p = Portfolio(bo, session_config, tqueue)

    # setup portfolio model for showing in table
    pmodel = PortfolioModel(p)
    ui.stock.setModel(pmodel)

    # setup and run jzWorker threads
    jzWorkerNum = 10
    worker = []
    for i in range(jzWorkerNum):
        s = jz.session(session_config)
        if not s.setup():
            print "Session setup failed."
            sys.exit(1)
        w = jzWorker(s, tqueue)
        worker.append(w)

    for i in range(jzWorkerNum):
        worker[i].start()

    # run the portfolio updater
    pupdater = PortfolioUpdater(shdbfn, shmapfn, szdbfn, szmapfn, p, pmodel)
    pupdater.start()

    # run the order info updater
    orderupdater = OrderUpdater(p, pmodel, session_config)
    orderupdater.start()

    # setup menu
    # window.connect(ui.import_portfolio, SIGNAL("activated()"), openfile)
    # window.connect(ui.buybatch, SIGNAL("activated()"), p.batchOrderSubmitBuy)
    window.connect(ui.buybatch, SIGNAL("activated()"), p.buybatch)
    window.connect(ui.pricelatest, SIGNAL("activated()"), p.pricelatest)
    window.connect(ui.prices1, SIGNAL("activated()"), p.prices1)
    window.connect(ui.prices2, SIGNAL("activated()"), p.prices2)
    window.connect(ui.prices3, SIGNAL("activated()"), p.prices3)
    window.connect(ui.prices4, SIGNAL("activated()"), p.prices4)
    window.connect(ui.prices5, SIGNAL("activated()"), p.prices5)
    window.connect(ui.priceb1, SIGNAL("activated()"), p.priceb1)
    window.connect(ui.priceb2, SIGNAL("activated()"), p.priceb2)
    window.connect(ui.priceb3, SIGNAL("activated()"), p.priceb3)
    window.connect(ui.priceb4, SIGNAL("activated()"), p.priceb4)
    window.connect(ui.priceb5, SIGNAL("activated()"), p.priceb5)
    window.connect(ui.cancel_order, SIGNAL("activated()"), p.cancelBatchOrder)
    window.connect(ui.gen_backuporder, SIGNAL("activated()"), p.genandsaveBackupOrder)

    window.show()
    app.exec_()
    print "notify threads to stop."
    pupdater.stop()
    orderupdater.stop()
    print "waiting threads to stop."
    pupdater.join()
    orderupdater.join()
    print "threas stopped."
    print "saving order info."
    p.saveBatchOrder(portfoliofn)
    del p
    del pupdater
    del orderupdater
    print "I will exit."

if __name__=="__main__":
    main(sys.argv)

