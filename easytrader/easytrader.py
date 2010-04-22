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
        # market code (SH, SZ), stock number, count
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
                # buy and sell records, list of dicts, with attributes defined next
                "pastbuy", "pastsell",
                # history stats for buy, not including current buying order, deduce from buy records
                "pastbuycount", "pastbuycost",
                # history stats for sell, not including current selling order, deduce from sell records
                "pastsellcount", "pastsellgain",
                # prices, update timely from dbf
                "latestprice", "tobuyprice", "tosellprice"]
        self.buyattr = [
                # current (last) buy specific fields
                "order_id", "order_state", "order_date", "order_time",
                "ordercount", "orderprice", "dealcount", "dealamount", # use amount as the money paid/gained
                "dealprice", "cancel_date", "cancel_time"]
        # assume buyattr is general enough 
        self.sellattr = self.buyattr
        # use market+stock number as key
        self.stockinfo = {}

        # TODO: model attributes
        self.stockmodelattr = ["count", "market", "code", "name",
                #"order_state", "ordercount", "dealcount", "orderprice",
                #"dealprice", "latestprice", "order_date", "order_time",
                "latestprice", "tobuyprice", "tosellprice"]
        # TODO: really need this assertion? how about derived attr
        # assert(set(self.stockmodelattr) <= set(self.stockattr+self.orderattr))

        # setup stock data and buy/sell records
        #self.bostate = Portfolio.BOUNORDERED
        #for i in stockbatch:
        #    if i[0] == "BO":
        #        self.bostate = i[3]
        #    else:
        #        scode = i[0].upper() + i[1]
        #        self.stocklist.append(scode)
        #        self.stockinfo.setdefault(scode, {})

        #        self.stockinfo[scode]["market"] = i[0].upper()
        #        self.stockinfo[scode]["code"] = i[1]
        #        self.stockinfo[scode]["count"] = i[2]
        #        self.stockinfo[scode]["order_state"] = Portfolio.UNORDERED
        #        self.stockinfo[scode]["order_id"] = ""
        #        self.stockinfo[scode]["order_date"] = ""
        #        self.stockinfo[scode]["order_time"] = ""
        #        try:
        #            self.stockinfo[scode]["order_state"] = i[3]
        #            self.stockinfo[scode]["order_id"] = i[4]
        #            self.stockinfo[scode]["order_date"] = i[5]
        #            self.stockinfo[scode]["order_time"] = i[6]
        #        except IndexError:
        #            pass
        #self.stockset = set(self.stocklist)

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

                self.stockinfo[scode]["market"] = i[0].upper()
                self.stockinfo[scode]["code"] = i[1]
                self.stockinfo[scode]["count"] = i[2]
                self.stockinfo[scode]["pastbuy"] = []
                self.stockinfo[scode]["pastsell"] = []
                try:
                    self.stockinfo[scode]["pastbuy"] = eval(i[3])
                    self.stockinfo[scode]["pastsell"] = eval(i[4])
                except IndexError:
                    pass
        f.close()
        self.stockset = set(self.stocklist)
        # TODO: also update pastbuycount/cost, pastsellcount/gain, etc.
        self.pastbuycount = 0
        self.pastbuycost = 0
        self.pastsellcount = 0
        self.pastsellgain = 0

    def savePortfolio(self, ptfn=None):
        if ptfn == None:
            f = open(self.ptfn, "wb")
        else:
            f = open(ptfn, "wb")
        writer = csv.writer(f)

        for scode in self.stocklist:
            si = self.stockinfo[scode]
            writer.writerow([si["market"], si["code"], si["count"], si["pastbuy"], si["pastsell"]])
        # portfolio state as a batch
        writer.writerow(["BO", self.bostate])
        f.flush()
        f.close()

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

            if( (boitem[0].upper() not in ["SH", "SZ", "BO"]) or (int(boitem[2])%100 != 0) ):
                badlines.append(line.strip())
                continue

            bo.append(boitem)
        f.close()
        return (bo, badlines)

    def saveBatchOrder(self, bofn=None):
        # TODO: alert if in buying or selling
        fn = bofn
        if bofn is None:
            fn = self.portfoliofn
        f = open(fn, "w")
        # stock info
        for scode in self.stocklist:
            si = self.stockinfo[scode]
            f.write(" ".join( (si["market"], si["code"], si["count"], si["order_state"],
                si["order_id"], si["order_date"], si["order_time"]) ))
            f.write("\n")
        # portfolio state as a batch
        f.write(" ".join( ("BO", "NA", "100", self.bostate) ))
        f.write("\n")
        f.flush()
        f.close()

    def buyBatchOrderSync(self, trdid):
        # NOTE: not maintained.
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
                    self.stockinfo[scode]["order_state"] = Portfolio.BUYSUCCESS
                else:
                    self.stockinfo[scode]["order_state"] = Portfolio.BUYFAILED

    def buyBatchOrderTop(self):
        trdcode = "0B"
        self.bolock.acquire()
        print "batch buying"

        if self.bostate == Portfolio.BOUNORDERED:
            # set Portfolio batch state
            self.bostate = Portfolio.BOBUYING
            self.bocount = 0

            # submit each stock order
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
        if resp.retcode == "0":
            self.stockinfo[scode]["order_id"] = resp.records[0][1]
            self.stockinfo[scode]["order_date"] = today
            self.stockinfo[scode]["order_time"] = str(datetime.now().time())
            self.stockinfo[scode]["order_state"] = Portfolio.BUYSUCCESS
            self.stockinfo[scode]["dealcount"] = "0"
        else:
            self.stockinfo[scode]["order_state"] = Portfolio.BUYFAILED

        self.bolock.acquire()
        self.bocount = self.bocount + 1
        if self.bocount == len(self.stocklist):
            self.bostate = Portfolio.BOBUYSUCCESS
            print "batch ordered"
        self.bolock.release()

    def cancelBuyBatchOrderSync(self):
        # NOTE: not maintained
        # only success orders can be canceled
        today = str(datetime.today().date())
        for scode in self.stocklist:
            if self.stockinfo[scode]["order_state"] == Portfolio.BUYSUCCESS and int(self.stockinfo[scode]["dealcount"]) < int(self.stockinfo[scode]["count"]):
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
                    self.stockinfo[scode]["cancel_date"] = today
                    self.stockinfo[scode]["cancel_time"] = str(datetime.now().time())
                    self.stockinfo[scode]["order_state"] = Portfolio.CANCELBUYSUCCESS
                else:
                    self.stockinfo[scode]["order_state"] = Portfolio.CANCELBUYFAILED
        # need update order state immediately. see cancelBatchOrderTop.
        self.bostate = Portfolio.BOBUYCANCELED

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
                if self.stockinfo[scode]["order_state"] == Portfolio.BUYSUCCESS and int(self.stockinfo[scode]["dealcount"]) < int(self.stockinfo[scode]["ordercount"]):
                    self.bocount = self.bocount + 1
                    param = {}
                    param["user_code"] = self.session["user_code"]
                    if self.stockinfo[scode]["market"] == "SH":
                        param["market"] = "10"
                    elif self.stockinfo[scode]["market"] == "SZ":
                        param["market"] = "00"
                    param["order_id"] = self.stockinfo[scode]["order_id"]
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
        if resp.retcode == "0":
            si["cancel_date"] = today
            si["cancel_time"] = str(datetime.now().time())
            si["order_state"] = Portfolio.CANCELBUYSUCCESS
        else:
            si["order_state"] = Portfolio.CANCELBUYFAILED

        # TODO: cancel may need time at exchange server
        # time.sleep(5)
        # update stock info immediately, it's important to use req.session, not self.session
        qoreq = jz.QueryOrderReq(req.session)
        qoreq["begin_date"] = si["order_date"]
        qoreq["end_date"] = si["order_date"]
        qoreq["get_orders_mode"] = "0" # all submissions
        qoreq["user_code"] = req.session["user_code"]
        # a bug in protocol/document results in next odd line
        qoreq["biz_no"] = si["order_id"]
        qoreq.send()
        qoresp = jz.QueryOrderResp(req.session)
        qoresp.recv()
        if qoresp.retcode == "0":
            si["dealcount"] = qoresp.records[0][-11]
            si["dealprice"] = qoresp.records[0][-1]
            si["ordercount"] = qoresp.records[0][15]

            if si["order_state"] == Portfolio.CANCELBUYFAILED:
                if si["dealcount"] == si["ordercount"]:
                    si["order_state"] = Portfolio.BUYSUCCESS
                else:
                    # TODO: change state to ORDERSUCCESS in this case too? to enable next cancel?
                    print "Error: cancel failed while dealcount is smaller than count."
        else:
            print "error when query order for %s" % si["order_id"]
            print qoresp.retcode, qoresp.retinfo

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
        self.buyBatchOrder("buy")

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
                stockinfo["tosellprice"] = self.getpricesh(rec, self.portfolio.buypolicy)
            elif stockinfo["market"] == "SZ":
                rec = dbsz[szmap[scode]]
                for f in self.szdbfield:
                    if type(rec[f]) is types.StringType:
                        stockinfo[self.szdbmapping[f]] = rec[f].decode("GBK")
                    else:
                        stockinfo[self.szdbmapping[f]] = rec[f]
                stockinfo["tobuyprice"] = self.getpricesz(rec, self.portfolio.buypolicy)
                stockinfo["tosellprice"] = self.getpricesz(rec, self.portfolio.buypolicy)

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
        # TODO: what if et is closed while tqueue is not empty
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
        ui.pricepolicylist.addItem(p.pricepolicynamemap[price])
    ui.pricepolicylist.setCurrentIndex(p.pricepolicylist.index(p.buypolicy))
    window.connect(ui.pricepolicylist, SIGNAL("currentIndexChanged(int)"), p.selpricepolicy)

    # setup batch order push button
    window.connect(ui.submitorder, SIGNAL("clicked()"), p.buybatch)
    window.connect(ui.cancelorder, SIGNAL("clicked()"), p.cancelBuyBatchOrder)
    window.connect(ui.genbackuporder, SIGNAL("clicked()"), p.genandsaveBackupOrder)
    window.connect(ui.saveorder, SIGNAL("clicked()"), p.saveBatchOrder)

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

