# -*- coding: utf-8 -*-

import os, sys
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
from PyQt4 import Qt
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
            hname = self.portfolio.stockmodelattr[section]
            try:
                hname = self.portfolio.stockattrnamemap[hname]
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
        rowkey = self.portfolio.stocklist[index.row()]
        columnkey = self.portfolio.stockmodelattr[index.column()]
        try:
            rawdata = self.portfolio.stockinfo[rowkey][columnkey]
            if not isinstance(rawdata, unicode):# expect rawdata as numbers here
                rawdata = str(rawdata)
            celldata = QString(rawdata)
            return QVariant(celldata)
        except KeyError:
            return QVariant()

    @pyqtSlot(int)
    def updaterow(self, rowindex):
        self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                self.index(rowindex,0),
                self.index(rowindex, len(self.portfolio.stockmodelattr)-1))

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

class Portfolio(object):

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
    BOUNORDERED = u"未委托"
    BOBUYING = u"正在买入"
    BOBUYSUCCESS = u"买入成功"
    BOBUYCANCELING = u"正在撤销买入"
    BOBUYCANCELED = u"买入已撤单"
    BOSELLING = u"正在卖出"
    BOSELLSUCCESS = u"卖出成功"
    BOSELLCANCELING = u"正在撤销卖出"
    BOSELLCANCELED = u"卖出已撤单"

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
                # pastxxxyyy are int/float types, others are string type, which is updated from messages
                # history stats for buy, not including current buying order, deduce from buy records
                "pastbuycount", "pastbuycost",
                # history stats for sell, not including current selling order, deduce from sell records
                "pastsellcount", "pastsellgain",
                # currentxxxyyy
                "currentbuycount", "currentbuycost",
                "currentsellcount", "currentsellgain",
                # prices, update timely from dbf
                "latestprice", "tobuyprice", "tosellprice"]

        # use market+stock number as key, dict of dict
        self.stockinfo = {}

        # TODO: model attributes
        self.stockmodelattr = ["count", "market", "code", "name",
                #"order_state", "ordercount", "dealcount", "orderprice",
                #"dealprice", "latestprice", "order_date", "order_time",
                "latestprice", "tobuyprice", "tosellprice",
                "currentbuycount", "currentbuycost", "currentsellcount", "currentsellgain"]

        self.stockattrnamemap = {
                "count":u"数量",
                "market":u"市场",
                "code":u"代码",
                "name":u"名称",
                "latestprice":u"最新价",
                "tobuyprice":u"建仓价",
                "tosellprice":u"平仓价",
                "currentbuycount":u"买入量",
                "currentbuycost":u"买入成本",
                "currentsellcount":u"卖出量",
                "currentsellgain":u"卖出获利"
                }
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

        self._bostate = Portfolio.BOUNORDERED

    def getbostate(self):
        return self._bostate

    @pyqtSlot()
    def setbostate(self, value):
        self._bostate = value
        try:
            # when Portfolio is being setup at initialization, it doesn't have uic attribute
            self.uic.showbostate()
        except AttributeError:
            pass

    # make bostate as property
    bostate = property(getbostate, setbostate)

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
                self.bostate = i[1].decode("utf-8")
            else:
                scode = i[0].upper() + i[1]
                self.stocklist.append(scode)
                self.stockinfo.setdefault(scode, {})

                si = self.stockinfo[scode]
                si["market"] = i[0].upper()
                si["code"] = i[1]
                si["count"] = i[2]
                si["pastbuy"] = []
                try:
                    buys = eval(i[3]) # including list of dict
                    for r in buys:
                        si["pastbuy"].append(OrderRecord(r))
                except IndexError:
                    pass
                si["pastsell"] = []
                try:
                    sells = eval(i[4]) # including list of dict
                    for r in sells:
                        si["pastsell"].append(OrderRecord(r))
                except IndexError:
                    pass
                si["pastbuycount"] = 0
                si["pastbuycost"] = 0.0
                si["pastsellcount"] = 0
                si["pastsellgain"] = 0.0
                # iterate pastbuy/sell and update pastxxxyyy
                for r in si["pastbuy"]:
                    if r["order_state"] == Portfolio.CANCELBUYSUCCESS:
                        si["pastbuycount"] = si["pastbuycount"] + int(r["dealcount"])
                        si["pastbuycost"] = si["pastbuycost"] + float(r["dealamount"])
                for r in si["pastsell"]:
                    if r["order_state"] == Portfolio.CANCELSELLSUCCESS:
                        si["pastsellcount"] = si["pastsellcount"] + int(r["dealcount"])
                        si["pastsellgain"] = si["pastsellgain"] + float(r["dealamount"])
                # update currentxxxyyy
                si["currentbuycount"] = si["pastbuycount"]
                si["currentbuycost"] = si["pastbuycost"]
                si["currentsellcount"] = si["pastsellcount"]
                si["currentsellgain"] = si["pastsellgain"]
                if len(si["pastsell"]) != 0:
                    if si["pastsell"][-1]["order_state"] == Portfolio.SELLSUCCESS:
                        if int(si["pastsell"][-1]["dealcount"]) < int(si["pastsell"][-1]["ordercount"]):
                            si["currentsellcount"] = si["pastsellcount"] + int(si["pastsell"][-1]["dealcount"])
                            si["currentsellgain"] = si["pastsellgain"] + float(si["pastsell"][-1]["dealcount"])
                        else:
                            si["pastsellcount"] = si["pastsellcount"] + int(si["pastsell"][-1]["dealcount"])
                            si["pastsellgain"] = si["pastsellgain"] + float(si["pastsell"][-1]["dealamount"])
                            si["currentsellcount"] = si["pastsellcount"]
                            si["currentsellgain"] = si["pastsellgain"]
                if len(si["pastbuy"]) != 0:
                    if si["pastbuy"][-1]["order_state"] == Portfolio.BUYSUCCESS:
                        if int(si["pastbuy"][-1]["dealcount"]) < int(si["pastbuy"][-1]["ordercount"]):
                            si["currentbuycount"] = si["pastbuycount"] + int(si["pastbuy"][-1]["dealcount"])
                            si["currentbuycost"] = si["pastbuycost"] + float(si["pastbuy"][-1]["dealcount"])
                        else:
                            si["pastbuycount"] = si["pastbuycount"] + int(si["pastbuy"][-1]["dealcount"])
                            si["pastbuycost"] = si["pastbuycost"] + float(si["pastbuy"][-1]["dealamount"])
                            si["currentbuycount"] = si["pastbuycount"]
                            si["currentbuycost"] = si["pastbuycost"]
        f.close()
        self.stockset = set(self.stocklist)

    def savePortfolio(self, ptfn=None):
        with self.bolock:
            if ptfn == None:
                f = open(self.ptfn, "wb")
            else:
                f = open(ptfn, "wb")
            writer = csv.writer(f)

            for scode in self.stocklist:
                si = self.stockinfo[scode]
                writer.writerow([si["market"], si["code"], si["count"], repr(si["pastbuy"]), repr(si["pastsell"])])
            # portfolio state as a batch
            writer.writerow(["BO", self.bostate.encode("utf-8")])
            f.flush()
            f.close()

    def buyBatchTop(self):
        self.bolock.acquire()
        print "batch buying", datetime.now().time()

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
                orec["ordercount"] = str( round100(int(si["count"]) - si["pastbuycount"]) )
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
                self.tqueue.put( (reqclass, respclass, param, self.buyBatchBottom, True) )

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
                    orec["ordercount"] = str( round100(int(si["count"]) - si["pastbuycount"]) )
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
                    self.tqueue.put( (reqclass, respclass, param, self.buyBatchBottom, True) )

            if self.bocount == 0:
                print "not stock to buy."
                self.bostate = Portfolio.BOBUYCANCELED

        else:
            print "not in buy-able state"

        self.bolock.release()

    buyBatch = buyBatchTop

    def buyBatchBottom(self, req, resp, param):
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
            print "batch buy-ed", datetime.now().time()
        self.bolock.release()

    def cancelBuyBatchTop(self):
        self.bolock.acquire()
        print "batch buy canceling"

        if self.bostate == Portfolio.BOBUYSUCCESS:
            # set Portfolio batch state
            self.bostate = Portfolio.BOBUYCANCELING
            self.bocount = 0

            # submit each stock order
            reqclass = jz.CancelOrderReq
            respclass = jz.CancelOrderResp
            for scode in self.stocklist:
                # only cancel (BUYSUCCESS and dealcount < ordercount) orders
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
                    # secu_code is needed at cancelBuyBatchBottom, not for CancelOrderReq
                    param["secu_code"] = self.stockinfo[scode]["code"]
                    self.tqueue.put( (reqclass, respclass, param, self.cancelBuyBatchBottom, True) )
            if self.bocount == 0:
                print "no stock to cancel buy"
                self.bostate = Portfolio.BOBUYSUCCESS
        else:
            print "not in buy cancel-able state"

        self.bolock.release()

    cancelBuyBatch = cancelBuyBatchTop

    def cancelBuyBatchBottom(self, req, resp, param):
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
        # update stock info immediately, it's important to use req.session,
        # not self.session, to make sure sqlite db object is used by only one thread
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
            # NOTE: the following update is left to OrderUpdater, otherwise
            #orec["dealcount"] = qoresp.records[-1][-11]
            #orec["dealamount"] = qoresp.records[-1][-9]
            #orec["dealprice"] = qoresp.records[-1][-1]

            dealcount = qoresp.records[-1][-11]
            if orec["order_state"] == Portfolio.CANCELBUYFAILED:
                if dealcount == orec["ordercount"]:
                    #assert int(si["count"]) == si["pastbuycount"] + int(orec["dealcount"])
                    orec["order_state"] = Portfolio.BUYSUCCESS
                else:
                    # TODO: change state to ORDERSUCCESS in this case too? to enable next cancel?
                    assert False, "Error: cancel failed while dealcount is smaller than count."
        else:
            assert False, "error when update order for %s (%s:%s)" % (si["order_id"], qoresp.retcode, qoresp.retinfo)

        # NOTE: the following update is left to OrderUpdater, otherwise
        # update pastbuyxxx
        #if orec["order_state"] in (Portfolio.BUYSUCCESS, Portfolio.CANCELBUYSUCCESS):
        #    # stock in Portfolio.BUYSUCCESS here is the one that's CANCELBUYFAILED
        #    si["pastbuycount"] = si["pastbuycount"] + int(orec["dealcount"])
        #    si["pastbuycost"] = si["pastbuycost"] + float(orec["dealamount"])
        #    si["currentbuycount"] = si["pastbuycount"]
        #    si["currentbuycost"] = si["pastbuycost"]

        self.bolock.acquire()
        self.bocount = self.bocount - 1
        if self.bocount == 0:
            self.bostate = Portfolio.BOBUYCANCELED
            print "batch buy canceled"
        self.bolock.release()

    def sellBatchTop(self):
        self.bolock.acquire()
        print "batch selling"

        if self.bostate == Portfolio.BOBUYSUCCESS:
            # only succeed when all buysuccess stocks are 100% buyed
            allbought = True
            for scode in self.stocklist:
                si = self.stockinfo[scode]
                orec = si["pastbuy"][-1]
                assert si["pastsell"] == []
                assert si["pastsellcount"] == 0
                if orec["order_state"] == Portfolio.BUYSUCCESS:
                    if orec["ordercount"] != orec["dealcount"]:
                        print "stock %s is in buying, cancel order fist and then sell." % scode
                        allbought = False
                        break
                    else:
                        assert int(si["count"]) == si["pastbuycount"]# + int(orec["dealcount"])
            if allbought == False:
                self.bolock.release()
                return

            # At this point, all stock in BUYSUCCESS is bought completely, and we update "pastbuyxxx" now
            # NOTE: the code is done at OrderUpdate
            #for scode in self.stocklist:
            #    si = self.stockinfo[scode]
            #    orec = si["pastbuy"][-1]
            #    if orec["order_state"] == Portfolio.BUYSUCCESS:
            #        si["pastbuycount"] = si["pastbuycount"] + int(orec["dealcount"])
            #        si["pastbuycost"] = si["pastbuycost"] + float(orec["dealamount"])

            # Now we sell BUYSUCCESS stocks
            reqclass = jz.SubmitOrderReq
            respclass = jz.SubmitOrderResp
            trdcode = "0S"
            self.bostate = Portfolio.BOSELLING
            self.bocount = 0
            for scode in self.stocklist:
                si = self.stockinfo[scode]
                orec = si["pastbuy"][-1]
                if orec["order_state"] == Portfolio.BUYSUCCESS:
                    # DO sell
                    self.bocount = self.bocount + 1
                    orec = OrderRecord()
                    orec["order_state"] = Portfolio.UNORDERED
                    orec["ordercount"] = str( si["pastbuycount"] - si["pastsellcount"] )
                    orec["orderprice"] = si["tosellprice"]
                    si["pastsell"].append(orec)

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
                    self.tqueue.put( (reqclass, respclass, param, self.sellBatchBottom, True) )
            if self.bocount == 0:
                print "no stock to sell"
                self.bostate = Portfolio.BOBUYSUCCESS

        elif self.bostate == Portfolio.BOBUYCANCELED:
            # sell stocks in CANCELBUYSUCCESS state and (BUYSUCCESS and 100% buy) state.
            # At this point, stock in BUYSUCCESS state should be bought completely.
            # first is some sanity check, and updating pastbuyxxx for BUYSUCCESS stocks
            for scode in self.stocklist:
                si = self.stockinfo[scode]
                assert si["pastsell"] == []
                assert si["pastsellcount"] == 0
                orec = si["pastbuy"][-1]
                if orec["order_state"] == Portfolio.BUYSUCCESS:
                    assert orec["ordercount"] == orec["dealcount"]
                    # only update pastbuyxxx for BUYSECCESS stocks
                    # NOTE: code is not necessary
                    #assert int(si["count"]) == si["pastbuycount"] + int(orec["dealcount"])
                    #si["pastbuycount"] = si["pastbuycount"] + int(orec["dealcount"])
                    #si["pastbuycost"] = si["pastbuycost"] + float(orec["dealamount"])
                elif orec["order_state"] == Portfolio.CANCELBUYSUCCESS:
                    assert int(orec["ordercount"]) > int(orec["dealcount"])
                    # pastbuycount is updated in cancelBuyBatchBottom for this case

            # Now we sell stocks
            reqclass = jz.SubmitOrderReq
            respclass = jz.SubmitOrderResp
            trdcode = "0S"
            self.bostate = Portfolio.BOSELLING
            self.bocount = 0
            for scode in self.stocklist:
                si = self.stockinfo[scode]
                orec = si["pastbuy"][-1]
                if orec["order_state"] in (Portfolio.BUYSUCCESS, Portfolio.CANCELBUYSUCCESS):
                    # DO sell
                    self.bocount = self.bocount + 1
                    orec = OrderRecord()
                    orec["order_state"] = Portfolio.UNORDERED
                    orec["ordercount"] = str( si["pastbuycount"] - si["pastsellcount"] )
                    orec["orderprice"] = si["tosellprice"]
                    si["pastsell"].append(orec)

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
                    self.tqueue.put( (reqclass, respclass, param, self.sellBatchBottom, True) )
            if self.bocount == 0:
                print "no stock to sell"
                self.bostate = Portfolio.BOBUYCANCELED

        elif self.bostate == Portfolio.BOSELLCANCELED:
            # At this point, pastsellxxx should be updated correctly.
            reqclass = jz.SubmitOrderReq
            respclass = jz.SubmitOrderResp
            trdcode = "0S"
            self.bostate = Portfolio.BOSELLING
            self.bocount = 0
            for scode in self.stocklist:
                si = self.stockinfo[scode]
                try:
                    orec = si["pastsell"][-1]
                except IndexError:
                    continue
                if orec["order_state"] == Portfolio.CANCELSELLSUCCESS:
                    # DO sell
                    self.bocount = self.bocount + 1
                    orec = OrderRecord()
                    orec["order_state"] = Portfolio.UNORDERED
                    orec["ordercount"] = str( si["pastbuycount"] - si["pastsellcount"] )
                    orec["orderprice"] = si["tosellprice"]
                    si["pastsell"].append(orec)

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
                    self.tqueue.put( (reqclass, respclass, param, self.sellBatchBottom, True) )
            if self.bocount == 0:
                print "no stock to sell"
                self.bostate = Portfolio.BOSELLCANCELED
        else:
            print "not in sell-able state"

        self.bolock.release()

    sellBatch = sellBatchTop

    def sellBatchBottom(self, req, resp, param):
        today = str(datetime.today().date())
        mkt = ""
        if param["market"] == "10":
            mkt = "SH"
        elif param["market"] == "00":
            mkt = "SZ"
        assert mkt != ""
        scode = mkt + param["secu_code"]
        orec = self.stockinfo[scode]["pastsell"][-1]
        if resp.retcode == "0":
            orec["order_id"] = resp.records[0][1]
            orec["order_state"] = Portfolio.SELLSUCCESS
            orec["order_date"] = today
            orec["order_time"] = str(datetime.now().time())
        else:
            orec["order_state"] = Portfolio.SELLFAILED

        self.bolock.acquire()
        self.bocount = self.bocount - 1
        if self.bocount == 0:
            self.bostate = Portfolio.BOSELLSUCCESS
            print "batch selled"
        self.bolock.release()

    def cancelSellBatchTop(self):
        self.bolock.acquire()
        print "batch sell canceling"

        if self.bostate == Portfolio.BOSELLSUCCESS:
            self.bostate = Portfolio.BOSELLCANCELING
            self.bocount = 0

            reqclass = jz.CancelOrderReq
            respclass = jz.CancelOrderResp
            for scode in self.stocklist:
                # only cancel (SELLSUCCESS and dealcount < ordercount) orders
                si = self.stockinfo[scode]
                try:
                    orec = si["pastsell"][-1]
                except IndexError:
                    continue
                if orec["order_state"] == Portfolio.SELLSUCCESS and int(orec["dealcount"]) < int(orec["ordercount"]):
                    self.bocount = self.bocount + 1
                    param = {}
                    param["user_code"] = self.session["user_code"]
                    if self.stockinfo[scode]["market"] == "SH":
                        param["market"] = "10"
                    elif self.stockinfo[scode]["market"] == "SZ":
                        param["market"] = "00"
                    param["order_id"] = orec["order_id"]
                    # secu_code is needed at cancelSellBatchBottom, not for CancelOrderReq
                    param["secu_code"] = self.stockinfo[scode]["code"]
                    self.tqueue.put( (reqclass, respclass, param, self.cancelSellBatchBottom, True) )

            if self.bocount == 0:
                print "no stock to cancel selling"
                self.bostate = Portfolio.BOSELLSUCCESS

        else:
            print "not in sell cancel-able state"

        self.bolock.release()

    cancelSellBatch = cancelSellBatchTop

    def cancelSellBatchBottom(self, req, resp, param):
        today = str(datetime.today().date())
        mkt = ""
        if param["market"] == "10":
            mkt = "SH"
        elif param["market"] == "00":
            mkt = "SZ"
        assert mkt != ""
        scode = mkt + param["secu_code"]

        si = self.stockinfo[scode]
        orec = si["pastsell"][-1]
        if resp.retcode == "0":
            orec["cancel_date"] = today
            orec["cancel_time"] = str(datetime.now().time())
            orec["order_state"] = Portfolio.CANCELSELLSUCCESS
        else:
            orec["order_state"] = Portfolio.CANCELSELLFAILED

        # update stock info immediately
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
            # NOTE: the following update is left to OrderUpdater, otherwise
            #orec["dealcount"] = qoresp.records[-1][-11]
            #orec["dealamount"] = qoresp.records[-1][-9]
            #orec["dealprice"] = qoresp.records[-1][-1]
            dealcount = qoresp.records[-1][-11]

            if orec["order_state"] == Portfolio.CANCELSELLFAILED:
                if dealcount == orec["ordercount"]:
                    # TODO: race condition here. also at cancel buy
                    #assert si["pastbuycount"] == si["pastsellcount"] + int(orec["dealcount"])
                    orec["order_state"] = Portfolio.SELLSUCCESS
                else:
                    assert False, "Error: cancel failed while dealcount is smaller than count."
        else:
            assert False, "error when update order for %s (%s:%s)" % (si["order_id"], qoresp.retcode, qoresp.retinfo)

        # NOTE: the following update is left to OrderUpdater, otherwise
        # update pastsellxxx
        #if orec["order_state"] in (Portfolio.SELLSUCCESS, Portfolio.CANCELSELLSUCCESS):
        #    si["pastsellcount"] = si["pastsellcount"] + int(orec["dealcount"])
        #    si["pastsellgain"] = si["pastsellgain"] + float(orec["dealamount"])
        #    si["currentsellcount"] = si["pastsellcount"]
        #    si["currentsellgain"] = si["pastsellgain"]

        self.bolock.acquire()
        self.bocount = self.bocount - 1
        if self.bocount == 0:
            self.bostate = Portfolio.BOSELLCANCELED
            print "batch sell canceled"
        self.bolock.release()

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
            with self.portfolio.bolock:
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

                # update a row
                rowindex = self.portfolio.stocklist.index(scode)
                QMetaObject.invokeMethod(self.portmodel, "updaterow", Qt.QueuedConnection,
                        Q_ARG("int", rowindex))
                #QMetaObject.invokeMethod(self.portmodel, "emit", Qt.QueuedConnection,
                #        Q_ARG(pyqtSignal, SIGNAL("dataChanged(QModelIndex,QModelIndex)")),
                #        Q_ARG(QModelIndex, self.portmodel.index(rowindex,0)),
                #        Q_ARG(QModelIndex, self.portmodel.index(rowindex, len(self.portfolio.stockmodelattr)-1)))

                #self.portmodel.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                #        self.portmodel.index(rowindex,0),
                #        self.portmodel.index(rowindex, len(self.portfolio.stockmodelattr)-1))

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
            with self.portfolio.bolock:
                si = self.portfolio.stockinfo[scode]
                # don't update buy if selled
                if len(si["pastsell"]) != 0:
                    order = si["pastsell"][-1]
                elif len(si["pastbuy"]) != 0:
                    order = si["pastbuy"][-1]
                else:
                    continue

                if order["order_id"] != "" and order["order_state"] in (Portfolio.BUYSUCCESS, Portfolio.SELLSUCCESS) and int(order["dealcount"]) < int(order["ordercount"]):
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
                        order["dealcount"] = qoresp.records[-1][-11]
                        order["dealamount"] = qoresp.records[-1][-9]
                        #try:
                        #    order["dealprice"] = str( float(qoresp.records[0][-9]) / float(qoresp.records[0][-11]) )
                        #except ZeroDivisionError:
                        #    order["dealprice"] = "0.00"
                        # TODO: dealprice is the average price? or last dealed price?
                        order["dealprice"] = qoresp.records[-1][-1]
                        #order["ordercount"] = qoresp.records[0][15]
                        # TODO: a quick patch, need refine update to pastxxx
                        #if order["ordercount"] == order["dealcount"]:
                        #    if len(si["pastsell"]) != 0:
                        #        si["pastsellcount"] = si["pastsellcount"] + int(order["dealcount"])
                        #        si["pastsellgain"] = si["pastsellgain"] + float(order["dealamount"])
                        #    else:
                        #        si["pastbuycount"] = si["pastbuycount"] + int(order["dealcount"])
                        #        si["pastbuycost"] = si["pastbuycost"] + float(order["dealamount"])
                        if int(order["dealcount"]) < int(order["ordercount"]):
                            # update pastxxx and currentxxx
                            if len(si["pastsell"]) != 0:
                                si["currentsellcount"] = si["pastsellcount"] + int(order["dealcount"])
                                si["currentsellgain"] = si["pastsellgain"] + float(order["dealamount"])
                            elif len(si["pastbuy"]) != 0:
                                si["currentbuycount"] = si["pastbuycount"] + int(order["dealcount"])
                                si["currentbuycost"] = si["pastbuycost"] + float(order["dealamount"])
                        else: # int(order["dealcount"]) == int(order["ordercount"])
                            if len(si["pastsell"]) != 0:
                                si["pastsellcount"] = si["pastsellcount"] + int(order["dealcount"])
                                si["pastsellgain"] = si["pastsellgain"] + float(order["dealamount"])
                                si["currentsellcount"] = si["pastsellcount"]
                                si["currentsellgain"] = si["pastsellgain"]
                            elif len(si["pastbuy"]) != 0:
                                si["pastbuycount"] = si["pastbuycount"] + int(order["dealcount"])
                                si["pastbuycost"] = si["pastbuycost"] + float(order["dealamount"])
                                si["currentbuycount"] = si["pastbuycount"]
                                si["currentbuycost"] = si["pastbuycost"]
                    else:
                        print "error when query order for %s" % order["order_id"]
                        print qoresp.retcode, qoresp.retinfo

                # update a row
                rowindex = self.portfolio.stocklist.index(scode)
                retval = QString()
                QMetaObject.invokeMethod(self.portmodel, "updaterow", Qt.QueuedConnection,
                        Q_ARG("int", rowindex))
                #self.portmodel.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                #        self.portmodel.index(rowindex,0),
                #        self.portmodel.index(rowindex, len(self.portfolio.stockmodelattr)-1))

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

class uicontrol(Ui_MainWindow):
    def __init__(self, mainwindow, portfolio, pmodel):
        self.mainwindow = mainwindow
        self.portfolio = portfolio
        self.pmodel = pmodel

        self.portfolio.uic = self

    def setup(self):
        self.setupUi(self.mainwindow)

        # setup stock info model
        self.stock.setModel(self.pmodel)

        # setup price combobox
        for price in self.portfolio.pricepolicylist:
            self.pricepolicybuy.addItem(self.portfolio.pricepolicynamemap[price])
            self.pricepolicysell.addItem(self.portfolio.pricepolicynamemap[price])
        self.pricepolicybuy.setCurrentIndex(self.portfolio.pricepolicylist.index(self.portfolio.buypolicy))
        self.pricepolicysell.setCurrentIndex(self.portfolio.pricepolicylist.index(self.portfolio.sellpolicy))
        self.mainwindow.connect(self.pricepolicybuy, SIGNAL("currentIndexChanged(int)"), self.setbuypricepolicy)
        self.mainwindow.connect(self.pricepolicysell, SIGNAL("currentIndexChanged(int)"), self.setsellpricepolicy)

        # setup batch order push button
        self.mainwindow.connect(self.buyorder, SIGNAL("clicked()"), self.buyBatch)
        self.mainwindow.connect(self.cancelbuyorder, SIGNAL("clicked()"), self.cancelBuyBatch)
        self.mainwindow.connect(self.sellorder, SIGNAL("clicked()"), self.sellBatch)
        self.mainwindow.connect(self.cancelsellorder, SIGNAL("clicked()"), self.cancelSellBatch)
        self.mainwindow.connect(self.saveorder_2, SIGNAL("clicked()"), self.savePortfolio)
        self.mainwindow.connect(self.saveorder, SIGNAL("clicked()"), self.savePortfolio)

        # update statusbar
        self.showbostate()

        #icon = QIcon()
        #icon.addPixmap(QPixmap("ztzq.ico"), QIcon.Normal, QIcon.Off)
        #print os.getcwd()
        #self.mainwindow.setWindowIcon(icon)

    @pyqtSlot()
    def buyBatch(self):
        self.portfolio.buyBatch()

    @pyqtSlot()
    def cancelBuyBatch(self):
        self.portfolio.cancelBuyBatch()

    @pyqtSlot()
    def sellBatch(self):
        self.portfolio.sellBatch()

    @pyqtSlot()
    def cancelSellBatch(self):
        self.portfolio.cancelSellBatch()

    @pyqtSlot()
    def savePortfolio(self):
        self.portfolio.savePortfolio()

    @pyqtSlot(int)
    def setbuypricepolicy(self, pindex):
        self.portfolio.buypolicy = self.portfolio.pricepolicylist[pindex]

    @pyqtSlot(int)
    def setsellpricepolicy(self, pindex):
        self.portfolio.sellpolicy = self.portfolio.pricepolicylist[pindex]

    def showbostate(self):
        QMetaObject.invokeMethod(self.statusbar, "showMessage", Qt.QueuedConnection, Q_ARG("QString", QString(u"组合状态: " + self.portfolio.bostate)))

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

def round100(n):
    return int(round(n/100.0)*100)

def main(args):
    #import psyco
    #psyco.full()

    # chdir to app's directory
    app = QApplication(args)
    os.chdir(os.path.dirname(os.path.abspath(args[0])))

    # read config
    session_config = {}
    session_config["tradedbfn"] = "tradeinfo.db"
    session_config["jzserver"] = "172.18.20.52"
    session_config["jzport"] = 9100
    session_config["jzaccount"] = "85804530"
    session_config["jzaccounttype"] = "Z"
    session_config["jzpasswd"] = "123444"

    # TODO: read last config from disk

    from logindiag import logindlg
    d = logindlg(session_config)
    d.show()
    d.exec_()
    if d.status == False:
        print "User cancel login"
        sys.exit(1)

    session_config.update(d.config)
    testsession = jz.session(session_config)
    if not testsession.setup():
        print "Cannot login."
        sys.exit(1)
    testsession.close()

    shdbfn = "z:\\show2003.dbf"
    szdbfn = "z:\\sjshq.dbf"
    shmapfn = "shmap.pkl"
    szmapfn = "szmap.pkl"
    if not verifymap(shdbfn, shmapfn, "S1"):
        print "SH stock map file error."
        sys.exit(1)
    if not verifymap(szdbfn, szmapfn, "HQZQDM"):
        print "SZ stock map file error."
        sys.exit(1)
    #portfoliofn = "hs300.txt"
    portfoliofn = unicode(QFileDialog.getOpenFileName(None, u"选择投资组合", "./portfolio", "*.ptf"))
    if portfoliofn == u"":
        print "No portfolio seleted."
        sys.exit(1)

    # setup portfolio
    tqueue = Queue.Queue()
    p = Portfolio(portfoliofn, session_config, tqueue)
    p.loadPortfolio()

    # setup portfolio model for showing in table
    pmodel = PortfolioModel(p)

    # run the portfolio updater
    pupdater = PortfolioUpdater(shdbfn, shmapfn, szdbfn, szmapfn, p, pmodel)
    pupdater.start()

    # run the order info updater
    orderupdater = OrderUpdater(p, pmodel, session_config)
    orderupdater.start()

    # setup and run jzWorker threads
    jzWorkerNum = 10
    workers = []
    for i in range(jzWorkerNum):
        w = jzWorker(session_config, tqueue)
        workers.append(w)

    for i in range(jzWorkerNum):
        workers[i].start()

    # main window
    window = QMainWindow()
    uic = uicontrol(window, p, pmodel)
    uic.setup()

    window.show()
    app.exec_()

    # exit process
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
