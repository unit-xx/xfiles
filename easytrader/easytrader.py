# -*- coding: utf-8 -*-

import sys
import csv
import socket
import pickle
import Queue
from threading import Thread, currentThread, Lock
import time
import types
from datetime import datetime

import jz
from dbfpy import dbf
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from tradeui import Ui_MainWindow

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
        # TODO: add order specific info
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

class OrderRecord:
    orattr = [
            # current (last) buy specific fields
            "order_id", "order_state", "order_date", "order_time",
            "ordercount", "orderprice", "dealcount", "dealamount", # use amount as the money paid/gained
            "dealprice", "cancel_date", "cancel_time"]

    def __init__(self, dictdata=None):
        self.data = {}
        self.data["order_id"] = ""
        self.data["order_state"] = Portfolio.INVALID
        self.data["order_date"] = ""
        self.data["order_time"] = ""
        self.data["ordercount"] = "0"
        self.data["orderprice"] = "0.0"
        self.data["dealcount"] = "0"
        self.data["dealamount"] = "0.0"
        self.data["dealprice"] = "0.0"
        self.data["cancel_date"] = ""
        self.data["cancel_time"] = ""
        if dictdata:
            self.data.update(dictdata)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __repr__(self):
        return repr(self.data)

class Portfolio:

    # stock states can be:
    INVALID = "INVALID"
    UNORDERED = "UNORDERED"
    # first is buy states
    BUYSUCCESS = "BUYSUCCESS"
    BUYFAILED = "BUYFAILED"
    # assumption: only success order can be canceled
    CANCELBUYSUCCESS = "CANCELBUYSUCCESS"
    CANCELBUYFAILED = "CANCELBUYFAILED"
    # next comes sell states
    SELLSUCCESS = "SELLSUCCESS"
    SELLFAILED = "SELLFAILED"
    CANCELSELLSUCCESS = "CANCELSELLSUCCESS"
    CANCELSELLFAILED = "CANCELSELLFAILED"


    # batch operation status
    BOUNORDERED = "BOUNORDERED"
    BOBUYING = "BOBUYING"
    BOBUYSUCCESS = "BOBUYSUCCESS"
    BOBUYCANCELING = "BOBUYCANCELING"
    BOBUYCANCELED = "BOBUYCANCELED"
    BOSELLING = "BOSELLING"
    BOSELLSUCCESS = "BOSELLSUCCESS"
    BOSELLCANCELING = "BOSELLCANCELING"
    BOSELLCANCELED = "BOSELLCANCELED"

    def __init__(self, ptfn, sessioncfg, tqueue):
        self.session = jz.session(sessioncfg)
        self.ptfn = ptfn
        if not self.session.setup():
            print "session setup failed."
            sys.exit(1)
        self.tqueue = tqueue
        self.bolock = Lock()

        # define stock data and buy/sell records attributes
        self.stocklist = []
        self.stockset = set()
        self.stockattr = [
                # common fields, read from storage, except name
                "count", "market", "code", "name",
                # buy and sell records, list of OrderRecord
                "pastbuy", "pastsell",
                # history stats for buy, not including current buying order, deduce from buy records
                # pastxxxyyy are int/float types, others are string type, which is updated from messages
                "pastbuycount", "pastbuycost",
                # history stats for sell, not including current selling order, deduce from sell records
                "pastsellcount", "pastsellgain",
                # prices, update timely from dbf
                "latestprice", "tobuyprice", "tosellprice"]

        # TODO: can be removed in face of OrderRecord class
        self.buyattr = [
                # current (last) buy specific fields
                "order_id", "order_state", "order_date", "order_time",
                "ordercount", "orderprice", "dealcount", "dealamount", # use amount as the money paid/gained
                "dealprice", "cancel_date", "cancel_time"]
        # assume buyattr is general enough 
        self.sellattr = self.buyattr

        # use market+stock number as key, dict of dict
        self.stockinfo = {}

        # TODO: model attributes
        self.stockmodelattr = ["count", "market", "code", "name",
                #"order_state", "ordercount", "dealcount", "orderprice",
                #"dealprice", "latestprice", "order_date", "order_time",
                "latestprice", "tobuyprice", "tosellprice"]
        # TODO: really need this assertion? how about derived attr
        # assert(set(self.stockmodelattr) <= set(self.stockattr+self.orderattr))

        # price policies
        self.pricepolicylist = ["latest", "s5", "s4", "s3", "s2", "s1", "b1", "b2", "b3", "b4", "b5"]
        self.buypolicy = "s5"
        self.sellpolicy = "b5"
        self.pricepolicynamemap = {"latest":u"最新价", 
                "s5":u"卖五",
                "s4":u"卖四",
                "s3":u"卖三",
                "s2":u"卖二",
                "s1":u"卖一",
                "b1":u"买一",
                "b2":u"买二",
                "b3":u"买三",
                "b4":u"买四",
                "b5":u"买五"
                }

    def __del__(self):
        self.session.close()

    def loadPortfolio(self, ptfn=None):
        """
        a .pfl file is a csv file which records
        mkt, code, count, buyrecords, sellrecords
        some special records are
        portfolio: BO, bostate
        option: OP, xxx, xxx
        """
        if ptfn == None:
            f = open(self.ptfn, "rb")
        else:
            f = open(ptfn, "rb")
        reader = csv.reader(f)
        self.bostate = Portfolio.BOUNORDERED
        for i in reader:
            assert(i[0] in ("BO", "SH", "SZ"))
            if i[0] == "BO":
                self.bostate = i[1]
            else:
                scode = i[0].upper() + i[1]
                self.stocklist.append(scode)
                self.stockinfo.setdefault(scode, {})

                si = self.stockinfo[scode]
                si["market"] = i[0].upper()
                si["code"] = i[1]
                si["count"] = i[2]
                si["pastbuy"] = []
                buys = eval(i[3]) # including list of dict
                for r in buys:
                    si["pastbuy"].append(OrderRecord(r))
                si["pastsell"] = []
                sells = eval(i[4]) # including list of dict
                for r in sells:
                    si["pastsell"].append(OrderRecord(r))
                si["pastbuycount"] = 0
                si["pastbuycost"] = 0.0
                si["pastsellcount"] = 0
                si["pastsellgain"] = 0.0
                # TODO: iterate pastbuy/sell and update pastxxxyyy
                for r in si["pastbuy"]:
                    pass
                for r in si["pastbuy"]:
                    pass
        f.close()
        self.stockset = set(self.stocklist)

    def savePortfolio(self, ptfn=None):
        # TODO: alert user if portfolio is in buying/selling state
        if ptfn == None:
            f = open(self.ptfn, "wb")
        else:
            f = open(ptfn, "wb")
        writer = csv.writer(f)

        for scode in self.stocklist:
            si = self.stockinfo[scode]
            writer.writerow([si["market"], si["code"], si["count"], repr(si["pastbuy"]), repr(si["pastsell"])])
        # portfolio state as a batch
        writer.writerow(["BO", self.bostate])
        f.flush()
        f.close()

    def buyBatchOrderTop(self):
        self.bolock.acquire()
        print "batch buying"

        if self.bostate == Portfolio.BOUNORDERED:
            # new and first batch buy order
            self.bostate = Portfolio.BOBUYING
            self.bocount = 0

            # submit each stock order
            reqclass = jz.SubmitOrderReq
            respclass = jz.SubmitOrderResp
            trdcode = "0B"
            for scode in self.stocklist:
                si = self.stockinfo[scode]
                assert si["pastbuy"] == []
                assert si["pastsell"] == []
                assert si["pastbuycount"] == 0
                assert si["pastbuycost"] == 0.0
                assert si["pastsellcount"] == 0
                assert si["pastsellgain"] == 0.0

                self.bocount = self.bocount + 1
                # TODO: is it possible that a req is queued but cannot be send?

                orec = OrderRecord()
                orec["order_state"] = Portfolio.UNORDERED
                orec["ordercount"] = str( (int(si["count"]) - si["pastbuycount"])/100*100 )
                orec["orderprice"] = si["tobuyprice"]
                si["pastbuy"].append(orec)

                param = {}
                param["user_code"] = self.session["user_code"]
                if si["market"] == "SH":
                    param["market"] = "10"
                    param["secu_acc"] = self.session["secu_acc"]["SH"]
                elif si["market"] == "SZ":
                    param["market"] = "00"
                    param["secu_acc"] = self.session["secu_acc"]["SZ"]
                param["account"] = self.session["account"]
                param["secu_code"] = si["code"]
                param["trd_id"] = trdcode
                param["price"] = orec["orderprice"]
                param["qty"] = orec["ordercount"]
                self.tqueue.put( (reqclass, respclass, param, self.buyBatchOrderBottom, True) )

            assert len(self.stockinfo) == self.bocount

        elif self.bostate == Portfolio.BOBUYCANCELED:
            # re-buy: only buy stock in CANCELBUYSUCCESS state
            self.bostate = Portfolio.BOBUYING
            self.bocount = 0

            reqclass = jz.SubmitOrderReq
            respclass = jz.SubmitOrderResp
            trdcode = "0B"
            for scode in self.stocklist:
                si = self.stockinfo[scode]
                if si["pastbuy"][-1]["order_state"] == Portfolio.CANCELBUYSUCCESS:
                    self.bocount = self.bocount + 1

                    orec = OrderRecord()
                    orec["order_state"] = Portfolio.UNORDERED
                    orec["ordercount"] = str( (int(si["count"]) - si["pastbuycount"])/100*100 )
                    orec["orderprice"] = si["tobuyprice"]
                    si["pastbuy"].append(orec)

                    param = {}
                    param["user_code"] = self.session["user_code"]
                    if si["market"] == "SH":
                        param["market"] = "10"
                        param["secu_acc"] = self.session["secu_acc"]["SH"]
                    elif si["market"] == "SZ":
                        param["market"] = "00"
                        param["secu_acc"] = self.session["secu_acc"]["SZ"]
                    param["account"] = self.session["account"]
                    param["secu_code"] = si["code"]
                    param["trd_id"] = trdcode
                    param["price"] = orec["orderprice"]
                    param["qty"] = orec["ordercount"]
                    self.tqueue.put( (reqclass, respclass, param, self.buyBatchOrderBottom, True) )

        else:
            print "not in buy-able state"

        self.bolock.release()

    buyBatchOrder = buyBatchOrderTop

    def buyBatchOrderBottom(self, req, resp, param):
        today = str(datetime.today().date())
        mkt = ""
        if param["market"] == "10":
            mkt = "SH"
        elif param["market"] == "00":
            mkt = "SZ"
        assert mkt != ""
        scode = mkt + param["secu_code"]
        orec = self.stockinfo[scode]["pastbuy"][-1]
        if resp.retcode == "0":
            orec["order_id"] = resp.records[0][1]
            orec["order_state"] = Portfolio.BUYSUCCESS
            orec["order_date"] = today
            orec["order_time"] = str(datetime.now().time())
        else:
            orec["order_state"] = Portfolio.BUYFAILED

        self.bolock.acquire()
        self.bocount = self.bocount - 1
        if self.bocount == 0:
            self.bostate = Portfolio.BOBUYSUCCESS
            print "batch ordered"
        self.bolock.release()

    def cancelBuyBatchOrderTop(self):
        self.bolock.acquire()
        print "batch canceling"

        if self.bostate == Portfolio.BOBUYSUCCESS:
            # set Portfolio batch state
            self.bostate = Portfolio.BOBUYCANCELING
            self.bocount = 0

            # submit each stock order
            reqclass = jz.CancelOrderReq
            respclass = jz.CancelOrderResp
            for scode in self.stocklist:
                # only cancel BUYSUCCESS and dealcount < ordercount orders
                si = self.stockinfo[scode]
                orec = si["pastbuy"][-1]
                if orec["order_state"] == Portfolio.BUYSUCCESS and int(orec["dealcount"]) < int(orec["ordercount"]):
                    self.bocount = self.bocount + 1
                    param = {}
                    param["user_code"] = self.session["user_code"]
                    if self.stockinfo[scode]["market"] == "SH":
                        param["market"] = "10"
                    elif self.stockinfo[scode]["market"] == "SZ":
                        param["market"] = "00"
                    param["order_id"] = orec["order_id"]
                    # secu_code is needed at cancelBuyBatchOrderBottom, not for CancelOrderReq
                    param["secu_code"] = self.stockinfo[scode]["code"]
                    self.tqueue.put( (reqclass, respclass, param, self.cancelBuyBatchOrderBottom, True) )
        else:
            print "not in cancel-able state"

        self.bolock.release()

    cancelBuyBatchOrder = cancelBuyBatchOrderTop

    def cancelBuyBatchOrderBottom(self, req, resp, param):
        today = str(datetime.today().date())
        mkt = ""
        if param["market"] == "10":
            mkt = "SH"
        elif param["market"] == "00":
            mkt = "SZ"
        assert mkt != ""
        scode = mkt + param["secu_code"]

        si = self.stockinfo[scode]
        orec = si["pastbuy"][-1]
        if resp.retcode == "0":
            orec["cancel_date"] = today
            orec["cancel_time"] = str(datetime.now().time())
            orec["order_state"] = Portfolio.CANCELBUYSUCCESS
        else:
            orec["order_state"] = Portfolio.CANCELBUYFAILED

        # TODO: cancel may need time at exchange server
        # time.sleep(5)
        # update stock info immediately, it's important to use req.session, not self.session
        qoreq = jz.QueryOrderReq(req.session)
        qoreq["begin_date"] = orec["order_date"]
        qoreq["end_date"] = orec["order_date"]
        qoreq["get_orders_mode"] = "0" # all submissions
        qoreq["user_code"] = req.session["user_code"]
        # a bug in protocol/document results in next odd line
        qoreq["biz_no"] = orec["order_id"]
        qoreq.send()
        qoresp = jz.QueryOrderResp(req.session)
        qoresp.recv()
        if qoresp.retcode == "0":
            orec["dealcount"] = qoresp.records[0][-11]
            orec["dealamount"] = qoresp.records[0][-9]
            # dealprice may not right
            orec["dealprice"] = qoresp.records[0][-1]

            if orec["order_state"] == Portfolio.CANCELBUYFAILED:
                if orec["dealcount"] == orec["ordercount"]:
                    orec["order_state"] = Portfolio.BUYSUCCESS
                else:
                    # TODO: change state to ORDERSUCCESS in this case too? to enable next cancel?
                    assert False, "Error: cancel failed while dealcount is smaller than count."
        else:
            assert False, "error when query order for %s (%s:%s)" % (si["order_id"], qoresp.retcode, qoresp.retinfo)

        # update pastbuyxxx
        if orec["order_state"] in (Portfolio.BUYSUCCESS, Portfolio.CANCELBUYSUCCESS):
            si["pastbuycount"] = si["pastbuycount"] + int(orec["dealcount"])
            si["pastbuycost"] = si["pastbuycost"] + float(orec["dealamount"])

        self.bolock.acquire()
        self.bocount = self.bocount - 1
        if self.bocount == 0:
            # TODO: cancel-able stock is not equal to total stock number
            self.bostate = Portfolio.BOBUYCANCELED
            print "batch canceled"
        self.bolock.release()

    def genBackupOrder(self):
        # now only consider CANCELBUYSUCCESS orders
        self.backuporder = {}
        self.backuporderlist = []
        backuporder = self.backuporder
        backuporderlist = self.backuporderlist
        for scode in self.stocklist:
            if self.stockinfo[scode]["order_state"] == Portfolio.CANCELBUYSUCCESS:
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
        self.buyBatchOrder()

    def selpricepolicy(self, pindex):
        self.buypolicy = self.pricepolicylist[pindex]

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
        self.shdbfield = ["S1", "S2", "S8"]#, "S9", "S10"]
        self.shdbmapping = {
                "S1":"code",
                "S2":"name",
                "S8":"latestprice"
                #"S9":"tobuyprice",
                #"S10":"tosellprice"
                }
        assert(len(self.shdbfield) == len(self.shdbmapping))

        # for SZ
        self.szdbfield = ["HQZQDM", "HQZQJC", "HQZJCJ"]#, "HQBJW1", "HQSJW1"]
        self.szdbmapping = {
                "HQZQDM":"code",
                "HQZQJC":"name",
                "HQZJCJ":"latestprice"
                #"HQBJW1":"tobuyprice",
                #"HQSJW1":"tosellprice"
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
        dbsh = self.dbsh
        dbsz = self.dbsz
        shmap = self.shmap
        szmap = self.szmap

        for scode in self.portfolio.stocklist:
            stockinfo = self.portfolio.stockinfo[scode]
            if stockinfo["market"] == "SH":
                rec = dbsh[shmap[scode]]
                for f in self.shdbfield:
                    if type(rec[f]) is types.StringType:
                        stockinfo[self.shdbmapping[f]] = rec[f].decode("GBK")
                    else:
                        stockinfo[self.shdbmapping[f]] = rec[f]
                stockinfo["tobuyprice"] = self.getpricesh(rec, self.portfolio.buypolicy)
                stockinfo["tosellprice"] = self.getpricesh(rec, self.portfolio.sellpolicy)
            elif stockinfo["market"] == "SZ":
                rec = dbsz[szmap[scode]]
                for f in self.szdbfield:
                    if type(rec[f]) is types.StringType:
                        stockinfo[self.szdbmapping[f]] = rec[f].decode("GBK")
                    else:
                        stockinfo[self.szdbmapping[f]] = rec[f]
                stockinfo["tobuyprice"] = self.getpricesz(rec, self.portfolio.buypolicy)
                stockinfo["tosellprice"] = self.getpricesz(rec, self.portfolio.sellpolicy)

        self.portmodel.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                self.portmodel.index(0,0), self.portmodel.index(
                    len(self.portfolio.stockinfo)-1,
                    len(self.portfolio.stockmodelattr)-1))

    def stop(self):
        self.runflag = False

    def run(self):
        while self.runflag:
            self.update()
            time.sleep(2)

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
            # don't update buy if selled
            if len(si["pastsell"]) != 0:
                order = si["pastsell"][-1]
            elif len(si["pastbuy"]) != 0:
                order = si["pastbuy"][-1]
            else:
                continue

            # TODO: only update buying/selling orders.
            if order["order_id"] != "":
                qoreq = jz.QueryOrderReq(self.session)
                qoreq["begin_date"] = order["order_date"]
                qoreq["end_date"] = order["order_date"]
                qoreq["get_orders_mode"] = "0" # all submissions
                qoreq["user_code"] = self.session["user_code"]
                # a bug in protocol/document results in next odd line
                qoreq["biz_no"] = order["order_id"]
                qoreq.send()
                qoresp = jz.QueryOrderResp(self.session)
                qoresp.recv()
                if qoresp.retcode == "0":
                    # TODO: don't know whether multi-line records case exists.
                    order["dealcount"] = qoresp.records[0][-11]
                    order["dealamount"] = qoresp.records[0][-9]
                    #try:
                    #    order["dealprice"] = str( float(qoresp.records[0][-9]) / float(qoresp.records[0][-11]) )
                    #except ZeroDivisionError:
                    #    order["dealprice"] = "0.00"
                    # TODO: dealprice is the average price? or last dealed price?
                    order["dealprice"] = qoresp.records[0][-1]
                    # TODO: ordercount may diff with count?
                    order["ordercount"] = qoresp.records[0][15]
                else:
                    print "error when query order for %s" % order["order_id"]
                    print qoresp.retcode, qoresp.retinfo

        self.portmodel.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                self.portmodel.index(0,0), self.portmodel.index(
                    len(self.portfolio.stockinfo)-1,
                    len(self.portfolio.stockmodelattr)-1))

    def stop(self):
        self.runflag = False

    def run(self):
        while self.runflag:
            self.update()
            time.sleep(2)

class jzWorker(Thread):
    def __init__(self, session_cfg, tqueue):
        Thread.__init__(self)
        self.session_cfg = session_cfg
        self.tqueue = tqueue
        self.runflag = True

    def setupsession(self):
        self.session = jz.session(self.session_cfg)
        if not self.session.setup():
            return False
        return True

    def closesession(self):
        self.session.close()

    def run(self):
        # TODO: what if easytrader is closed while tqueue is not empty
        if not self.setupsession():
            print "jzWorker", currentThread().ident, "cannot setup session, and will exit."
            return

        while self.runflag:
            try:
                t = self.tqueue.get(True, 2)
                self.dotask(t)
                self.tqueue.task_done()
            except Queue.Empty:
                pass

        self.session.close()

    def dotask(self, t):
        """
        t is a task as a tuple:
        (request class, response class, param, callback, ifstoretrade)

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
        ifstoretrade = t[4]
        if ifstoretrade:
            self.session.storetrade(req, resp)
        callback(req, resp, param)

    def stop(self):
        self.runflag = False

def testslot(t):
    print t

def verifymap(dbfn, mapfn, codekey):
    db = dbf.Dbf(dbfn, ignoreErrors=True, readOnly=True)
    f = open(mapfn)
    map = pickle.load(f)
    ret = True
    for k in map:
        # k is sth like SH600000, SZ000338
        if k[2:] != db[map[k]][codekey]:
            print k, map[k], db[map[k]]
            ret = False
            break
    f.close()
    db.close()
    return ret

def main(args):
    #import psyco
    #psyco.full()

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
        sys.exit(1)
    if not verifymap(szdbfn, szmapfn, "HQZQDM"):
        print "Stock map file error."
        sys.exit(1)
    #portfoliofn = "hs300.txt"
    portfoliofn = unicode(QFileDialog.getOpenFileName(None, u"选择投资组合", "./portfolio", "*.ptf"))

    session_config = {}
    session_config["tradedbfn"] = "tradeinfo.db"
    session_config["jzserver"] = "172.18.20.52"
    session_config["jzport"] = 9100
    session_config["jzaccount"] = "85804530"
    session_config["jzaccounttype"] = "Z"
    session_config["jzpasswd"] = "123444"

    # setup portfolio
    tqueue = Queue.Queue()
    p = Portfolio(portfoliofn, session_config, tqueue)
    p.loadPortfolio()

    # setup portfolio model for showing in table
    pmodel = PortfolioModel(p)
    ui.stock.setModel(pmodel)

    # setup and run jzWorker threads
    jzWorkerNum = 10
    workers = []
    for i in range(jzWorkerNum):
        w = jzWorker(session_config, tqueue)
        workers.append(w)

    for i in range(jzWorkerNum):
        workers[i].start()

    # run the portfolio updater
    pupdater = PortfolioUpdater(shdbfn, shmapfn, szdbfn, szmapfn, p, pmodel)
    pupdater.start()

    # run the order info updater
    orderupdater = OrderUpdater(p, pmodel, session_config)
    orderupdater.start()

    # setup price combobox
    # TODO: add sell case
    for price in p.pricepolicylist:
        ui.pricepolicybuy.addItem(p.pricepolicynamemap[price])
    ui.pricepolicybuy.setCurrentIndex(p.pricepolicylist.index(p.buypolicy))
    window.connect(ui.pricepolicybuy, SIGNAL("currentIndexChanged(int)"), p.selpricepolicy)

    # setup batch order push button
    window.connect(ui.buyorder, SIGNAL("clicked()"), p.buybatch)
    window.connect(ui.cancelbuyorder, SIGNAL("clicked()"), p.cancelBuyBatchOrder)
    window.connect(ui.genbackuporder, SIGNAL("clicked()"), p.genandsaveBackupOrder)
    window.connect(ui.saveorder_2, SIGNAL("clicked()"), p.savePortfolio)
    window.connect(ui.saveorder, SIGNAL("clicked()"), p.savePortfolio)

    window.show()
    app.exec_()
    print "notify updater threads to stop."
    pupdater.stop()
    orderupdater.stop()
    print "waiting updater threads to stop."
    pupdater.join()
    orderupdater.join()
    print "updater threads stopped."
    print "waiting jzWorkers to finalize jobs"
    # next line ensures all async request will be executed before exit.
    tqueue.join()
    for i in range(jzWorkerNum):
        workers[i].stop()
    for i in range(jzWorkerNum):
        workers[i].join()
    print "jzWorkers stopped"
    print "saving order info."
    p.savePortfolio()
    del p
    del pupdater
    del orderupdater
    print "I will exit."

if __name__=="__main__":
    main(sys.argv)

