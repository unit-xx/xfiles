# -*- coding: utf-8 -*-

import os, sys
import csv
import socket
import pickle
import Queue
import ConfigParser
#from mx import Queue
import cProfile
from threading import Thread, currentThread, Lock
from binascii import unhexlify
import time
from datetime import datetime
import types
from ctypes import *
import logging, logging.config

import jz, jsd
import jsdhq
from dbfpy import dbf
from PyQt4 import Qt
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from tradeui import Ui_MainWindow
from stockquery import stockquerydlg
from positioninfo import positioninfodlg

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

class StockIndexModel(QAbstractTableModel):
    def __init__(self, portfolio, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.portfolio = portfolio

    def rowCount(self, parent):
        return 1

    def columnCount(self, parent):
        return len(self.portfolio.sindexmodelattr)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            hname = self.portfolio.sindexmodelattr[section]
            try:
                hname = self.portfolio.sindexattrnamemap[hname]
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
        columnkey = self.portfolio.sindexmodelattr[index.column()]
        try:
            rawdata = self.portfolio.sindexinfo[columnkey]
            if not isinstance(rawdata, unicode):# expect rawdata as numbers here
                rawdata = str(rawdata)
            celldata = QString(rawdata)
            return QVariant(celldata)
        except KeyError:
            return QVariant()

    @pyqtSlot()
    def updaterow(self):
        self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                self.index(0,0),
                self.index(0, len(self.portfolio.sindexmodelattr)-1))

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

class SIndexRecord:
    sirattr = [
            "order_id", "order_state", "order_date", "ordertime",
            "ordercount", "orderprice" "openclose", "longshort", "ifhedge",
            "orderseat", "syscenter",
            "dealcount", "dealprice", "canceldate", "canceltime"]

    def __init__(self, dictdata=None):
        self.data = {}
        self.data["order_id"] = ""
        self.data["order_state"] = Portfolio.IFUNORDERED
        self.data["order_date"] = ""
        self.data["order_time"] = ""
        self.data["ordercount"] = "0"
        self.data["orderprice"] = "0.0"

        self.data["openclose"] = "0"
        self.data["longshort"] = "0"
        self.data["ifhedge"] = "0"

        self.data["orderseat"] = ""
        self.data["syscenter"] = ""

        self.data["dealcount"] = "0"
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

    IFUNORDERED = u"未持仓"
    IFOPENSHORTOK = u"空开成功"
    IFOPENSHORTFAILED = u"空开失败"
    IFCANCELOPENSHORTOK = u"取消空开成功"
    IFCANCELOPENSHORTFAILED = u"取消空开失败"
    IFCLOSESHORTOK = u"空平成功"
    IFCLOSESHORTFAILED = u"空平失败"
    IFCANCELCLOSESHORTOK = u"取消空平成功"
    IFCANCELCLOSESHORTFAILED = u"取消空平失败"

    IFOPENLONGOK = u"多开成功"
    IFOPENLONGFAILED = u"多开失败"
    IFCANCELOPENLONGOK = u"取消多开成功"
    IFCANCELOPENLONGFAILED = u"取消多开失败"
    IFCLOSELONGOK = u"多平成功"
    IFCLOSELONGFAILED = u"多平失败"
    IFCANCELCLOSELONGOK = u"取消多平成功"
    IFCANCELCLOSELONGFAILED = u"取消多平失败"

    def __init__(self, ptfn, sessioncfg, tqueue, updtlock, jsdcfg):
        # TODO: change to use jsdworker
        self.session = jz.session(sessioncfg)
        self.ptfn = ptfn
        self.logger = logging.getLogger()
        if not self.session.setup():
            self.logger.warning("session setup failed.")
            sys.exit(1)
        self.tqueue = tqueue
        self.bolock = Lock()
        self.sindexlock = Lock()

        self.updtlock = updtlock

        # define stock data and buy/sell records attributes
        self.stocklist = []
        self.stockset = set()
        self.stockattr = [
                # common fields, read from storage, except name, of type str/unicode
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
                # prices, update timely from dbf, of type float
                "latestprice", "tobuyprice", "tosellprice",
                "open", "close",
                # of type float (after conversion from jz)
                "ceiling", "floor",
                # of type boolean
                "stopped"]
        self.buypricefix = 0.00
        self.sellpricefix = 0.00

        # use market+stock number as key, dict of dict
        self.stockinfo = {}

        # TODO: model attributes
        self.stockmodelattr = ["count", "market", "code", "name",
                #"order_state", "ordercount", "dealcount", "orderprice",
                #"dealprice", "latestprice", "order_date", "order_time",
                "close", "open",
                "latestprice", "tobuyprice", "tosellprice",
                "currentbuycount", "currentbuycost", "currentsellcount", "currentsellgain"]
        assert set(self.stockmodelattr) <= set(self.stockattr)

        self.stockattrnamemap = {
                "count":u"数量",
                "market":u"市场",
                "code":u"代码",
                "name":u"名称",
                "close":u"昨收",
                "open":u"今开",
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

        self.sindexattr = ["count", "code",
                # of type float
                "latestprice", "open", "close", "ceiling", "floor",
                # of type float
                "openposprice", "closeposprice",
                # of type SIndexRecord
                "pastopen", "pastclose",
                "opencount", "closecount", "earning",
                "stopped", "state"]
        self.sindexmodelattr = ["count", "code",
                "latestprice", "close", "open", "ceiling", "floor",
                "openposprice", "closeposprice",
                "opencount", "closecount", "earning",
                "state"]
        # need state? or just a replication of order_state of last order
        assert set(self.sindexmodelattr) <= set(self.sindexattr)
        self.sindexattrnamemap = {
                "count":u"数量",
                "code":u"代码",
                "latestprice":u"最新价",
                "close":u"昨收",
                "open":u"今开",
                "ceiling":u"涨停",
                "floor":u"跌停",
                "openposprice":u"开仓价",
                "closeposprice":u"平仓价",
                "stopped":u"停牌",
                "opencount":u"建仓量",
                "closecount":u"平仓量",
                "earning":u"盈亏",
                "state":u"状态"
                }
        self.sindexinfo = {}
        self.sindexpricepolicylist = ["latest", "s1", "b1"]
        self.openpolicy = "b1"
        self.closepolicy = "s1"
        self.sindexstate = Portfolio.IFUNORDERED
        self.openpricefix = 0.0
        self.closepricefix = 0.0
        self.jsdcfg = jsdcfg
        s = jsd.session(self.jsdcfg)
        if not s.setup():
            self.logger.warning("Cannot login")
        self.jsdsession = s

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

    def close(self):
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
            assert(i[0] in ("BO", "IF", "SH", "SZ"))
            if i[0] == "BO":
                self.bostate = i[1].decode("utf-8")
            elif i[0] == "IF":
                self.sindexinfo["code"] = i[1].upper()
                self.sindexinfo["count"] = i[2]
                self.sindexinfo["state"] = Portfolio.IFUNORDERED
                try:
                    self.sindexinfo["state"] = i[3].decode("utf-8")
                except IndexError:
                    pass
                self.sindexinfo["pastopen"] = []
                try:
                    opens = eval(i[4])
                    for r in opens:
                        self.sindexinfo["pastopen"].append(SIndexRecord(r))
                except IndexError:
                    pass
                self.sindexinfo["pastclose"] = []
                try:
                    closes = eval(i[5])
                    for r in closes:
                        self.sindexinfo["pastclose"].append(SIndexRecord(r))
                except IndexError:
                    pass
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
                            si["currentsellgain"] = si["pastsellgain"] + float(si["pastsell"][-1]["dealamount"])
                        else:
                            si["pastsellcount"] = si["pastsellcount"] + int(si["pastsell"][-1]["dealcount"])
                            si["pastsellgain"] = si["pastsellgain"] + float(si["pastsell"][-1]["dealamount"])
                            si["currentsellcount"] = si["pastsellcount"]
                            si["currentsellgain"] = si["pastsellgain"]
                if len(si["pastbuy"]) != 0:
                    if si["pastbuy"][-1]["order_state"] == Portfolio.BUYSUCCESS:
                        if int(si["pastbuy"][-1]["dealcount"]) < int(si["pastbuy"][-1]["ordercount"]):
                            si["currentbuycount"] = si["pastbuycount"] + int(si["pastbuy"][-1]["dealcount"])
                            si["currentbuycost"] = si["pastbuycost"] + float(si["pastbuy"][-1]["dealamount"])
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

            # write IF first
            try:
                writer.writerow(["IF", self.sindexinfo["code"], self.sindexinfo["count"],
                    self.sindexinfo["state"].encode("utf-8"), self.sindexinfo["pastopen"],
                    self.sindexinfo["pastclose"]])
            except KeyError:# no sif info
                pass
            for scode in self.stocklist:
                si = self.stockinfo[scode]
                writer.writerow([si["market"], si["code"], si["count"], repr(si["pastbuy"]), repr(si["pastsell"])])
            # portfolio state as a batch
            writer.writerow(["BO", self.bostate.encode("utf-8")])
            f.flush()
            f.close()

    def buyBatchTop(self):
        self.bolock.acquire()
        self.logger.info("batch buying")

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
                self.logger.info("not stock to buy.")
                self.bostate = Portfolio.BOBUYCANCELED

        else:
            self.logger.info("not in buy-able state")

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
            orec["order_state"] = Portfolio.BUYSUCCESS
            orec["order_date"] = today
            orec["order_time"] = str(datetime.now().time())
            orec["order_id"] = resp.records[0][1]
        else:
            orec["order_state"] = Portfolio.BUYFAILED

        self.bolock.acquire()
        self.bocount = self.bocount - 1
        if self.bocount == 0:
            self.bostate = Portfolio.BOBUYSUCCESS
            self.logger.info("batch buy-ed")
        self.bolock.release()

    def cancelBuyBatchTop(self):
        self.bolock.acquire()
        self.logger.info("batch buy canceling")

        if self.bostate == Portfolio.BOBUYSUCCESS:
            # set Portfolio batch state
            self.bostate = Portfolio.BOBUYCANCELING
            self.bocount = 0

            # submit each stock order
            reqclass = jz.CancelOrderReq
            respclass = jz.CancelOrderResp

            # block update to ALL orders
            self.updtlock.acquire()

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
                self.logger.info("no stock to cancel buy")
                self.bostate = Portfolio.BOBUYSUCCESS
                # no work to do, let OrderUpdater go on.
                self.updtlock.release()
        else:
            self.logger.info("not in buy cancel-able state")

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
            dealcount, dealamount, dealprice = qoresp.getTotal()
            orec["dealcount"] = str(dealcount)
            orec["dealamount"] = str(dealamount)
            orec["dealprice"] = str(dealprice)
            if orec["order_state"] == Portfolio.CANCELBUYFAILED:
                if orec["dealcount"] == orec["ordercount"]:
                    assert int(si["count"]) == si["pastbuycount"] + int(orec["dealcount"])
                    orec["order_state"] = Portfolio.BUYSUCCESS
                else:
                    # TODO: change state to ORDERSUCCESS in this case too? to enable next cancel?
                    assert False, "Error: cancel failed while dealcount is smaller than count."
        else:
            assert False, "error when update order for %s (%s:%s)" % (si["order_id"], qoresp.retcode, qoresp.retinfo)

        # update pastbuyxxx
        if orec["order_state"] in (Portfolio.BUYSUCCESS, Portfolio.CANCELBUYSUCCESS):
            # stock in Portfolio.BUYSUCCESS here is the one that's CANCELBUYFAILED
            si["pastbuycount"] = si["pastbuycount"] + int(orec["dealcount"])
            si["pastbuycost"] = si["pastbuycost"] + float(orec["dealamount"])
            si["currentbuycount"] = si["pastbuycount"]
            si["currentbuycost"] = si["pastbuycost"]

        self.bolock.acquire()
        self.bocount = self.bocount - 1
        if self.bocount == 0:
            self.updtlock.release()
            self.bostate = Portfolio.BOBUYCANCELED
            self.logger.info("batch buy canceled")
        self.bolock.release()

    def sellBatchTop(self):
        self.bolock.acquire()
        self.logger.info("batch selling")

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
                        self.logger.info("stock %s is in buying, cancel order fist and then sell." % scode)
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
                self.logger.info("no stock to sell")
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
                self.logger.info("no stock to sell")
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
                self.logger.info("no stock to sell")
                self.bostate = Portfolio.BOSELLCANCELED
        else:
            self.logger.info("not in sell-able state")

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
            orec["order_state"] = Portfolio.SELLSUCCESS
            orec["order_date"] = today
            orec["order_time"] = str(datetime.now().time())
            orec["order_id"] = resp.records[0][1]
        else:
            orec["order_state"] = Portfolio.SELLFAILED

        self.bolock.acquire()
        self.bocount = self.bocount - 1
        if self.bocount == 0:
            self.bostate = Portfolio.BOSELLSUCCESS
            self.logger.info("batch selled")
        self.bolock.release()

    def cancelSellBatchTop(self):
        self.bolock.acquire()
        self.logger.info("batch sell canceling")

        if self.bostate == Portfolio.BOSELLSUCCESS:
            self.bostate = Portfolio.BOSELLCANCELING
            self.bocount = 0

            reqclass = jz.CancelOrderReq
            respclass = jz.CancelOrderResp

            # block update to ALL orders
            self.updtlock.acquire()

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
                self.logger.info("no stock to cancel selling")
                self.bostate = Portfolio.BOSELLSUCCESS
                # no work to do, let OrderUpdater go on.
                self.updtlock.release()
        else:
            self.logger.info("not in sell cancel-able state")

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
            dealcount, dealamount, dealprice = qoresp.getTotal()
            orec["dealcount"] = str(dealcount)
            orec["dealamount"] = str(dealamount)
            orec["dealprice"] = str(dealprice)
            if orec["order_state"] == Portfolio.CANCELSELLFAILED:
                if orec["dealcount"] == orec["ordercount"]:
                    assert si["pastbuycount"] == si["pastsellcount"] + int(orec["dealcount"])
                    orec["order_state"] = Portfolio.SELLSUCCESS
                else:
                    assert False, "Error: cancel failed while dealcount is smaller than count."
        else:
            assert False, "error when update order for %s (%s:%s)" % (si["order_id"], qoresp.retcode, qoresp.retinfo)

        # update pastsellxxx
        if orec["order_state"] in (Portfolio.SELLSUCCESS, Portfolio.CANCELSELLSUCCESS):
            si["pastsellcount"] = si["pastsellcount"] + int(orec["dealcount"])
            si["pastsellgain"] = si["pastsellgain"] + float(orec["dealamount"])
            si["currentsellcount"] = si["pastsellcount"]
            si["currentsellgain"] = si["pastsellgain"]

        self.bolock.acquire()
        self.bocount = self.bocount - 1
        if self.bocount == 0:
            self.updtlock.release()
            self.bostate = Portfolio.BOSELLCANCELED
            self.logger.info("batch sell canceled")
        self.bolock.release()

    def openshort(self):
        with self.sindexlock:
            if self.sindexstate == Portfolio.IFUNORDERED:
                oreq = jsd.OrderReq(self.jsdsession)
                oreq["exchcode"] = jsd.CFFEXCODE
                oreq["code"] = self.sindexinfo["code"]
                oreq["longshort"] = "1"
                oreq["openclose"] = "0"
                oreq["ifhedge"] = "0"
                oreq["count"] = self.sindexinfo["count"]
                oreq["price"] = self.sindexinfo["openposprice"]
                oreq["clientnum"] = self.jsdsession["clientnum"]
                oreq["seat"] = self.jsdsession["seat"]
                oreq.send()
                oresp = jsd.OrderResp(self.jsdsession)
                oresp.recv()
                sirec = SIndexRecord()
                if oresp.anwser == "Y":
                    # NOTE: order state may change after ordering
                    resp = oresp.records[0]
                    sirec["order_id"] = resp[1]
                    sirec["order_state"] = Portfolio.IFOPENSHORTOK
                    sirec["order_date"] = str(datetime.today().date())
                    sirec["order_time"] = str(datetime.now().time())
                    sirec["ordercount"] = resp[14]
                    sirec["orderprice"] = resp[15]
                    sirec["openclose"] = "0"
                    sirec["longshort"] = "1"
                    sirec["ifhedge"] = "0"
                    sirec["orderseat"] = resp[30]
                    sirec["syscenter"] = resp[19]
                    # TODO: test storetrade ok
                    self.sindexinfo["pastopen"].append(sirec)
                elif oresp.anwser == "N":
                    resp = oresp.records[0]
                    sirec["order_state"] = Portfolio.IFOPENSHORTFAILED
                    sirec["order_date"] = str(datetime.today().date())
                    sirec["order_time"] = str(datetime.now().time())
                    sirec["ordercount"] = oreq["count"]
                    sirec["orderprice"] = oreq["price"]
                    sirec["openclose"] = "0"
                    sirec["longshort"] = "1"
                    sirec["ifhedge"] = "0"
                    # TODO: test storetrade ok
                    self.sindexinfo["pastopen"].append(sirec)
                else:
                    self.logger.warning("unknow order response: %s" % str(oresp.records))

            elif self.sindexstate == Portfolio.IFCANCELOPENSHORTOK:
                pass
            else:
                pass

    def cancelopenshort(self):
        with self.sindexlock:
            if self.sindexstate == Portfolio.IFOPENSHORTOK:
                pass
            else:
                pass

    def closeshort(self):
        with self.sindexlock:
            if self.sindexstate == Portfolio.IFOPENSHORTOK:
                pass
            elif self.sindexstate == Portfolio.IFCANCELOPENSHORTOK:
                pass
            elif self.sindexstate == Portfolio.IFCANCELCLOSESHORTOK:
                pass
            else:
                pass

    def cancelcloseshort(self):
        with self.sindexlock:
            if self.sindexstate == Portfolio.IFCLOSESHORTOK:
                pass
            else:
                pass

class ProfiledThread(Thread):
    # Overrides threading.Thread.run()
    def run(self):
        profiler = cProfile.Profile()
        try:
            print "run run"
            return profiler.runcall(Thread.run, self)
        finally:
            print "dumping stats"
            profiler.dump_stats('myprofile-%d.profile' % (self.ident,))

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
        self.name = "PortfolioUpdater"
        self.logger = logging.getLogger()

        # one-to-one mapping of dbfield to stockattr, for SH
        self.shdbfield = ["S1", "S2", "S3", "S4", "S8"]#, "S9", "S10"]
        self.shdbmapping = {
                "S1":"code",
                "S2":"name",
                "S3":"close",
                "S4":"open",
                "S8":"latestprice"
                }
        assert(len(self.shdbfield) == len(self.shdbmapping))

        # for SZ
        self.szdbfield = ["HQZQDM", "HQZRSP", "HQJRKP", "HQZQJC", "HQZJCJ"]#, "HQBJW1", "HQSJW1"]
        self.szdbmapping = {
                "HQZQDM":"code",
                "HQZQJC":"name",
                "HQZRSP":"close",
                "HQJRKP":"open",
                "HQZJCJ":"latestprice"
                }
        assert(len(self.szdbfield) == len(self.szdbmapping))

    def close(self):
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
        price = shrec[policymapping[pricepolicy]]
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
        price = szrec[policymapping[pricepolicy]]
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
                stockinfo["tobuyprice"] = self.getpricesh(rec, self.portfolio.buypolicy) + self.portfolio.buypricefix
                stockinfo["tosellprice"] = self.getpricesh(rec, self.portfolio.sellpolicy) + self.portfolio.sellpricefix
            elif stockinfo["market"] == "SZ":
                rec = dbsz[szmap[scode]]
                for f in self.szdbfield:
                    if type(rec[f]) is types.StringType:
                        stockinfo[self.szdbmapping[f]] = rec[f].decode("GBK")
                    else:
                        stockinfo[self.szdbmapping[f]] = rec[f]
                stockinfo["tobuyprice"] = self.getpricesz(rec, self.portfolio.buypolicy) + self.portfolio.buypricefix
                stockinfo["tosellprice"] = self.getpricesz(rec, self.portfolio.sellpolicy) + self.portfolio.sellpricefix

            # update a row
            rowindex = self.portfolio.stocklist.index(scode)
            QMetaObject.invokeMethod(self.portmodel, "updaterow", Qt.QueuedConnection,
                    Q_ARG("int", rowindex))

    def stop(self):
        self.runflag = False

    def run(self):
        self.update()
        while self.runflag:
            time.sleep(2)
            self.update()

class SIFPriceUpdater_poll(Thread):
    def __init__(self, portfolio, sindexmodel, jsdcfg, uic):
        Thread.__init__(self)
        self.portfolio = portfolio
        self.sindexmodel = sindexmodel
        self.jsdcfg = jsdcfg
        self.jsdsession = None
        self.uic = uic
        self.runflag = True
        self.logger = logging.getLogger()
        self.name = "SIFPriceUpdater"

    def close(self):
        if self.jsdsession:
            self.jsdsession.close()

    def update(self):
        hqreq = jsd.QueryHQReq(self.jsdsession)
        #hqreq["exchcode"] = "G"
        hqreq["code"] = self.portfolio.sindexinfo["code"]
        hqreq.send()
        hqresp = jsd.QueryHQResp(self.jsdsession)
        hqresp.recv()
        if hqresp.anwser == "Y":
            self.portfolio.sindexinfo["latestprice"] = float(hqresp.records[0][9])
            self.portfolio.sindexinfo["open"] = float(hqresp.records[0][6])
            self.portfolio.sindexinfo["close"] = float(hqresp.records[0][5])
            self.portfolio.sindexinfo["ceiling"] = float(hqresp.records[0][17])
            self.portfolio.sindexinfo["floor"] = float(hqresp.records[0][18])
            self.portfolio.sindexinfo["openposprice"] = self.getsindexprice(hqresp.records[0], self.portfolio.openpolicy) + self.portfolio.openpricefix
            self.portfolio.sindexinfo["closeposprice"] = self.getsindexprice(hqresp.records[0], self.portfolio.closepolicy) + self.portfolio.closepricefix

            QMetaObject.invokeMethod(self.sindexmodel, "updaterow", Qt.QueuedConnection)
            # TODO: also update earnings for stock index

    def getsindexprice(self, hqrecord, pricepolicy):
        policymapping = {
                "latest":9,
                "b1":13,
                "s1":14
                }
        return float(hqrecord[policymapping[pricepolicy]])

    def stop(self):
        self.runflag = False

    def run(self):
        # setup session
        s = jsd.session(self.jsdcfg)
        if not s.setup():
            self.logger.warning("Cannot login")
            return False
        self.jsdsession = s

        # ... and run periodic update
        self.update()
        self.uic.stockindex.resizeColumnsToContents()
        while self.runflag:
            time.sleep(1)
            self.update()

        self.close()

class SIFPriceUpdater_pushee(Thread):
    def __init__(self, portfolio, sindexmodel, jsdcfg, uic):
        Thread.__init__(self)
        self.portfolio = portfolio
        self.sindexmodel = sindexmodel
        self.jsdcfg = jsdcfg
        self.jsdsession = None
        self.uic = uic
        self.runflag = True
        self.logger = logging.getLogger()
        self.name = "SIFPriceUpdater"

    def updateprice(self, quotaData, qcount):
        for i in range(qcount):
            qd = quotaData[i]
            si = self.portfolio.sindexinfo
            if qd.varity_code+qd.deliv_date == si["code"]:
                si["latestprice"] = qd.lastPrice
                si["open"] = qd.openPrice
                si["close"] = qd.preClosePrice
                si["ceiling"] = qd.upperLimitPrice
                si["floor"] = qd.lowerLimitPrice
                si["openposprice"] = self.getsindexprice(qd, self.portfolio.openpolicy) + self.portfolio.openpricefix
                si["closeposprice"] = self.getsindexprice(qd, self.portfolio.closepolicy) + self.portfolio.closepricefix

        QMetaObject.invokeMethod(self.sindexmodel, "updaterow", Qt.QueuedConnection)
        # TODO: also update earnings for stock index

    def getsindexprice(self, qd, pricepolicy):
        policymapping = {
                "latest":"lastPrice",
                "b1":"bidPrice1",
                "s1":"askPrice1"
                }
        return getattr(qd, policymapping[pricepolicy])

    def stop(self):
        self.runflag = False

    def run(self):
        os.environ["PATH"] = "".join([os.environ["PATH"], ";", self.jsdcfg["hqdllpath"]])
        dll = WinDLL(self.jsdcfg["hqdll"])
        prototype = WINFUNCTYPE(c_bool, c_ushort, c_char_p)
        KSFTHQPUB_Start = prototype(("KSFTHQPUB_Start", dll))

        prototype = WINFUNCTYPE(None)
        KSFTHQPUB_Stop = prototype(("KSFTHQPUB_Stop", dll))

        prototype = WINFUNCTYPE(c_int, c_char_p, c_int, c_int, c_char_p)
        KSFTHQPUB_GetQuota = prototype(("KSFTHQPUB_GetQuota", dll))

        errmsg = create_string_buffer(1024)
        ret = KSFTHQPUB_Start(int(self.jsdcfg["hqport"]), errmsg)
        if not ret:
            self.logger.warning("Error while start receiving hq: %s", errmsg)
            return

        timeout = 2000 # 2sec
        jsdhq.MAX_QUOTA_ITEM_COUNT = 50
        quotaData = (jsdhq.KSFT_QUOTA_PUBDATA_ITEM * jsdhq.MAX_QUOTA_ITEM_COUNT)()
        while self.runflag:
            qcount = KSFTHQPUB_GetQuota(cast(quotaData, c_char_p),
                    sizeof(jsdhq.KSFT_QUOTA_PUBDATA_ITEM)*jsdhq.MAX_QUOTA_ITEM_COUNT,
                    timeout,
                    errmsg)
            if qcount < 0:
                self.logging.warning("Error while receiving hq: %s", errmsg)
            elif qcount > 0:
                self.updateprice(quotaData, qcount)
                self.uic.stockindex.resizeColumnsToContents()
            else:
                pass

        KSFTHQPUB_Stop()

SIFPriceUpdater = SIFPriceUpdater_pushee

class SIFOrderUpdater(Thread):
    def __init__(self, portfolio, sindexmodel, jsdcfg):
        Thread.__init__(self)
        self.portfolio = portfolio
        self.sindexmodel = sindexmodel
        self.jsdcfg = jsdcfg
        self.sindexlock = portfolio.sindexlock
        self.name = "SIFOrderUpdater"
        self.logger = logging.getLogger()
        self.session = None
        self.runflag = True

    def close(self):
        if self.session:
            self.session.close()

    def update(self):
        with self.sindexlock:
            si = self.portfolio.sindexinfo
            if len(si["pastclose"]) != 0:
                order = si["pastclose"][-1]
            elif len(si["pastopen"]) != 0:
                order = si["pastopen"][-1]
            else:
                pass

            if order["order_id"] != "" and order["order_state"] in ("nsap") and int(order["dealcount"]) < int(order["ordercount"]):
                    pass

    def stop(self):
        self.runflag = False

    def run(self):
        s = jsd.session(self.jsdcfg)
        if not s.setup():
            self.logger.warning("Cannot login")
            return False
        self.session = s

        while self.runflag:
            self.update()
            time.sleep(1)

        self.close()

class SIFOrderPushee(Thread):
    def __init__(self, portfolio, sindexmodel, jsdcfg):
        Thread.__init__(self)
        self.portfolio = portfolio
        self.sindexmodel = sindexmodel
        self.jsdcfg = jsdcfg
        self.sindexlock = portfolio.sindexlock
        self.name = "SIFOrderPushee"
        self.logger = logging.getLogger()
        self.session = None
        self.runflag = True
        self.conn = None
        self.msghandler = {
                8020:self.pinghdl
                }

    def pinghdl(self, cmd, length):
        print cmd, length

    def defaulthdl(self, cmd, length):
        print cmd, length
        data = self.conn.recv(length)
        print data

    def close(self):
        if self.conn:
            self.conn.close()

    def setup(self):
        ret = True
        self.conn = socket.socket()
        try:
            self.conn.connect((self.jsdcfg["jsdserver"],
                self.jsdcfg["jsdport"]+2))
        except socket.error:
            self.logging.warning("cannot connect to push address")
            ret = False
        self.conn.settimeout(10)
        return ret

    def update(self):
        with self.sindexlock:
            try:
                data = self.conn.recv(4)
                print len(data), data
                cmd = data[0:2]
                length = data[2:4]
            except socket.timeout:
                print "timeout"

        # TODO: send ping message, and recv pong
        # TODO: can only work without htons, why?
        self.conn.send(unhexlify("%04x" % (20)))
        self.conn.send(unhexlify("%04x" % (0)))
        data = self.conn.recv(4)

    def stop(self):
        self.runflag = False

    def run(self):
        if not self.setup():
            return

        # send connect signal
        self.conn.send(unhexlify("%04x" % (1)))
        self.conn.send(unhexlify("%04x" % (0)))
        while self.runflag:
            self.update()

        self.close()


class OrderUpdater(Thread):
    def __init__(self, portfolio, portmodel, sessioncfg, updtlock):
        Thread.__init__(self)
        self.portfolio = portfolio
        self.portmodel = portmodel
        self.runflag = True
        self.session = jz.session(sessioncfg)
        self.updtlock = updtlock
        self.name = "OrderUpdater"
        self.logger = logging.getLogger()
        # TODO: session setup here is not right, dbconn will be
        # created in mainthread, which is wrong.
        # the bug is not triggered in realrun because we don't
        # store anything in OrderUpdater
        if not self.session.setup():
            self.logger.warning("Session setup failed.")
            sys.exit(1)

    def close(self):
        if self.session:
            self.session.close()

    def update(self):
        for scode in self.portfolio.stocklist:
            with self.updtlock:
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
                        dealcount, dealamount, dealprice = qoresp.getTotal()
                        order["dealcount"] = str(dealcount)
                        order["dealamount"] = str(dealamount)
                        order["dealprice"] = str(dealprice)
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
                        self.logger.warning("error when query order for %s: %s, %s"
                                % (order["order_id"], qoresp.retcode, qoresp.retinfo))

                # update a row
                rowindex = self.portfolio.stocklist.index(scode)
                QMetaObject.invokeMethod(self.portmodel, "updaterow", Qt.QueuedConnection,
                        Q_ARG("int", rowindex))

    def stop(self):
        self.runflag = False

    def run(self):
        while self.runflag:
            self.update()
            time.sleep(2)

class asyncWorker(Thread):
    def __init__(self, session_cfg, tqueue):
        Thread.__init__(self)
        self.session_cfg = session_cfg
        self.tqueue = tqueue
        self.runflag = True
        self.name = "jzWorker"
        self.logger = logging.getLogger()
        self.session = None

    def setupsession(self):
        return False

    def closesession(self):
        if self.session:
            self.session.close()

    def myrun(self):
        # TODO: what if easytrader is closed while tqueue is not empty
        if not self.setupsession():
            self.logger.warning("cannot setup session, and will exit.")
            return

        while self.runflag:
            try:
                t = self.tqueue.get(True, 2)
                self.dotask(t)
                self.tqueue.task_done()
            except Queue.Empty:
                pass

        #while self.runflag:
        #    if self.tqueue:
        #        t = self.tqueue.pop()
        #        self.dotask(t)
        #    else:
        #        time.sleep(0.05)

        self.closesession()

    def profiledrun(self):
        profiler = cProfile.Profile()

        try:
            return profiler.runcall(self.myrun)
        finally:
            profiler.dump_stats('myprofile-%d.profile' % (self.ident,))

    run = myrun

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

class jzWorker(asyncWorker):
    def __init__(self, session_cfg, tqueue):
        asyncWorker.__init__(self, session_cfg, tqueue)
        self.runflag = True
        self.name = "jzWorker"

    def setupsession(self):
        self.session = jz.session(self.session_cfg)
        if not self.session.setup():
            return False
        return True

class jsdWorker(asyncWorker):
    def __init__(self, session_cfg, tqueue):
        asyncWorker.__init__(self, session_cfg, tqueue)
        self.runflag = True
        self.name = "jsdWorker"

    def setupsession(self):
        self.session = jsd.session(self.session_cfg)
        if not self.session.setup():
            return False
        return True

class uicontrol(Ui_MainWindow):
    def __init__(self, mainwindow, session_cfg, portfolio, pmodel, sindexmodel):
        self.mainwindow = mainwindow
        self.session_cfg = session_cfg
        self.portfolio = portfolio
        self.pmodel = pmodel
        self.sindexmodel = sindexmodel
        self.portfolio.uic = self

        self.logger = logging.getLogger()

    def setup(self):
        self.setupUi(self.mainwindow)

        # setup stock info model
        self.stock.setModel(self.pmodel)
        self.stock.resizeColumnsToContents()
        self.stockindex.setModel(self.sindexmodel)

        # setup stock price combobox
        for price in self.portfolio.pricepolicylist:
            self.pricepolicybuy.addItem(self.portfolio.pricepolicynamemap[price])
            self.pricepolicysell.addItem(self.portfolio.pricepolicynamemap[price])
        self.pricepolicybuy.setCurrentIndex(self.portfolio.pricepolicylist.index(self.portfolio.buypolicy))
        self.pricepolicysell.setCurrentIndex(self.portfolio.pricepolicylist.index(self.portfolio.sellpolicy))
        self.mainwindow.connect(self.pricepolicybuy, SIGNAL("currentIndexChanged(int)"), self.setbuypricepolicy)
        self.mainwindow.connect(self.pricepolicysell, SIGNAL("currentIndexChanged(int)"), self.setsellpricepolicy)

        # setup sif price combobox
        for price in self.portfolio.sindexpricepolicylist:
            self.openpricecmbox.addItem(self.portfolio.pricepolicynamemap[price])
            self.closepricecmbox.addItem(self.portfolio.pricepolicynamemap[price])
        self.openpricecmbox.setCurrentIndex(self.portfolio.sindexpricepolicylist.index(self.portfolio.openpolicy))
        self.closepricecmbox.setCurrentIndex(self.portfolio.sindexpricepolicylist.index(self.portfolio.closepolicy))
        self.mainwindow.connect(self.openpricecmbox, SIGNAL("currentIndexChanged(int)"), self.setopenpricepolicy)
        self.mainwindow.connect(self.closepricecmbox, SIGNAL("currentIndexChanged(int)"), self.setclosepricepolicy)

        # setup buy/sell batch price fix
        self.portfolio.buypricefix = self.buypricefixspin.value()
        self.portfolio.sellpricefix = self.sellpricefixspin.value()
        self.mainwindow.connect(self.buypricefixspin, SIGNAL("valueChanged(double)"), self.setbuypricefix)
        self.mainwindow.connect(self.sellpricefixspin, SIGNAL("valueChanged(double)"), self.setsellpricefix)

        # setup stock index open/close price fix
        self.portfolio.openpricefix = self.openpricefixspin.value()
        self.portfolio.closepricefix = self.closepricefixspin.value()
        self.mainwindow.connect(self.openpricefixspin, SIGNAL("valueChanged(double)"), self.setopenpricefix)
        self.mainwindow.connect(self.closepricefixspin, SIGNAL("valueChanged(double)"), self.setclosepricefix)

        # setup batch order push button
        self.mainwindow.connect(self.buyorder, SIGNAL("clicked()"), self.buyBatch)
        self.mainwindow.connect(self.cancelbuyorder, SIGNAL("clicked()"), self.cancelBuyBatch)
        self.mainwindow.connect(self.sellorder, SIGNAL("clicked()"), self.sellBatch)
        self.mainwindow.connect(self.cancelsellorder, SIGNAL("clicked()"), self.cancelSellBatch)
        self.mainwindow.connect(self.saveorder_2, SIGNAL("clicked()"), self.savePortfolio)
        self.mainwindow.connect(self.saveorder, SIGNAL("clicked()"), self.savePortfolio)

        # setup stock index button
        self.mainwindow.connect(self.opensifbtn, SIGNAL("clicked()"), self.openshort)

        # setup menu
        self.mainwindow.connect(self.stockinfoact, SIGNAL("triggered()"), self.showstockinfo)
        self.mainwindow.connect(self.posstatact, SIGNAL("triggered()"), self.showposstat)

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
    def openshort(self):
        self.portfolio.openshort()

    @pyqtSlot()
    def savePortfolio(self):
        self.portfolio.savePortfolio()

    @pyqtSlot(int)
    def setbuypricepolicy(self, pindex):
        self.portfolio.buypolicy = self.portfolio.pricepolicylist[pindex]

    @pyqtSlot(int)
    def setsellpricepolicy(self, pindex):
        self.portfolio.sellpolicy = self.portfolio.pricepolicylist[pindex]

    @pyqtSlot(int)
    def setopenpricepolicy(self, pindex):
        self.portfolio.openpolicy = self.portfolio.sindexpricepolicylist[pindex]

    @pyqtSlot(int)
    def setclosepricepolicy(self, pindex):
        self.portfolio.closepolicy = self.portfolio.sindexpricepolicylist[pindex]

    @pyqtSlot(float)
    def setbuypricefix(self, value):
        self.portfolio.buypricefix = value

    @pyqtSlot(float)
    def setsellpricefix(self, value):
        self.portfolio.sellpricefix = value

    @pyqtSlot(float)
    def setopenpricefix(self, value):
        self.portfolio.openpricefix = value

    @pyqtSlot(float)
    def setclosepricefix(self, value):
        self.portfolio.closepricefix = value

    @pyqtSlot()
    def showstockinfo(self):
        sqdlg = stockquerydlg(self.session_cfg)
        if sqdlg.setup():
            sqdlg.show()
            sqdlg.activateWindow()
            QMetaObject.invokeMethod(sqdlg.refresh, "clicked", Qt.QueuedConnection)
            sqdlg.exec_()
        else:
            QMessageBox.information(None, "", u"不能登录")

    @pyqtSlot()
    def showposstat(self):
        pidlg = positioninfodlg(self.portfolio)
        pidlg.setup()
        QMetaObject.invokeMethod(pidlg.refresh, "clicked", Qt.QueuedConnection)
        pidlg.exec_()

    def showbostate(self):
        QMetaObject.invokeMethod(self.statusbar, "showMessage", Qt.QueuedConnection, Q_ARG("QString", QString(u"组合状态: " + self.portfolio.bostate)))

class basediffUpdater(Thread):
    def __init__(self, shdbfn, shmapfn, jsdcfg, uic):
        Thread.__init__(self)
        self.runflag = True

        self.shdbfn = shdbfn
        self.shmapfn = shmapfn
        self.jsdcfg = jsdcfg
        self.jsdsession = None
        self.uic = uic

        self.name = "basediffUpdater"
        self.logger = logging.getLogger()

    def run(self):
        hs300code = "SH000300"

        self.dbsh = dbf.Dbf(self.shdbfn, ignoreErrors=True, readOnly=True)
        f = open(self.shmapfn)
        self.shmap = pickle.load(f)
        f.close()

        self.jsdsession = jsd.session(self.jsdcfg)
        if not self.jsdsession.setup():
            self.logger.warning("jsd session setup failed.")
        
        # read contracts and fill stock index combobox.
        self.sicontracts = ['IF1006', 'IF1007', 'IF1009', 'IF1012']
        for sindex in self.sicontracts:
            self.uic.sindexcmbox.addItem(sindex)
        self.uic.sindexcmbox.setCurrentIndex(0)

        while self.runflag:
            # update hs300
            rec = self.dbsh[self.shmap[hs300code]]
            hs300latest = rec['S8']

            # update selected stock index
            # TODO: use hq pushee
            hqreq = jsd.QueryHQReq(self.jsdsession)
            hqreq["exchcode"] = jsd.CFFEXCODE
            hqreq["code"] = self.sicontracts[self.uic.sindexcmbox.currentIndex()]
            hqreq.send()
            hqresp = jsd.QueryHQResp(self.jsdsession)
            hqresp.recv()
            if hqresp.anwser == "N":
                continue
            silatest = float(hqresp.records[0][9])

            # calculate basediff
            basediff = silatest - hs300latest

            # update UI
            self.uic.hs300line.setText(str(hs300latest))
            self.uic.sindexline.setText(str(silatest))
            self.uic.basediffline.setText(str(basediff))

            time.sleep(1)

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

    # main initialization

    app = QApplication(args)
    # chdir to app's directory
    os.chdir(os.path.dirname(os.path.abspath(args[0])))
    # make log directory
    CONFIGFN = "easytrader.cfg"
    LOGDIR = "log"
    if not os.path.isdir(LOGDIR):
        try:
            os.mkdir(LOGDIR)
        except OSError as e:
            print "cannot make log directory: %d, %s." % (e.errno, e.strerror)
            QMessageBox.information(None, "", u"不能创建log目录: %d, %s" % (e.errno, e.strerror))
            sys.exit(1)

    logging.config.fileConfig(CONFIGFN)
    logger = logging.getLogger()
    msg = "i'm started"
    logger.info("========================")
    logger.info(msg)

    # read config
    JZSEC = "jz"
    JSDSEC = "jsd"

    session_config = {}
    session_config["tradedbfn"] = "tradeinfo.db"
    session_config["jzserver"] = "172.18.20.52"
    session_config["jzport"] = 9100
    session_config["jzaccount"] = "85804530"
    session_config["jzaccounttype"] = "Z"
    session_config["jzpasswd"] = "123444"
    session_config["shdbfn"] = "z:\\show2003.dbf"
    session_config["szdbfn"] = "z:\\sjshq.dbf"
    config = ConfigParser.RawConfigParser()
    config.read(CONFIGFN)
    for k,v in config.items(JZSEC):
        session_config[k] = v
    try:
        session_config["jzport"] = int(session_config["jzport"])
    except KeyError:
        pass

    # show config in dialog
    from logindiag import logindlg
    d = logindlg(session_config)
    d.show()
    d.activateWindow()
    d.exec_()
    if d.status == False:
        logger.info("User cancel login")
        sys.exit(1)

    session_config.update(d.config)
    testsession = jz.session(session_config)
    if not testsession.setup():
        logger.warning("Cannot login.")
        sys.exit(1)
    testsession.close()

    # verify stock mapping
    shdbfn = session_config["shdbfn"]
    szdbfn = session_config["szdbfn"]
    shmapfn = "shmap.pkl"
    szmapfn = "szmap.pkl"
    if not verifymap(shdbfn, shmapfn, "S1"):
        logger.warning("SH stock map file error.")
        sys.exit(1)
    if not verifymap(szdbfn, szmapfn, "HQZQDM"):
        logger.warning("SZ stock map file error.")
        sys.exit(1)

    # save config
    #for k in session_config:
    #    config.set("easytrader", k, session_config[k])
    #config.write(configfn)

    #load portfolio
    portfoliofn = unicode(QFileDialog.getOpenFileName(None, u"选择投资组合", "./portfolio", "*.ptf"))
    if portfoliofn == u"":
        logger.info("No portfolio seleted.")
        sys.exit(1)

    # get jsd session config
    jsd_sessioncfg = {}
    for k,v in config.items(JSDSEC):
        jsd_sessioncfg[k] = v
    try:
        jsd_sessioncfg["jsdport"] = int(jsd_sessioncfg["jsdport"])
    except KeyError:
        pass

    updtlock = Lock()
    # setup portfolio
    tqueue = Queue.Queue()
    p = Portfolio(portfoliofn, session_config, tqueue, updtlock, jsd_sessioncfg)
    p.loadPortfolio()

    # setup portfolio model for showing in table
    pmodel = PortfolioModel(p)
    sindexmodel = StockIndexModel(p)

    # run the portfolio updater
    pupdater = PortfolioUpdater(shdbfn, shmapfn, szdbfn, szmapfn, p, pmodel)
    pupdater.start()

    # run the order info updater
    orderupdater = OrderUpdater(p, pmodel, session_config, updtlock)
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
    uic = uicontrol(window, session_config, p, pmodel, sindexmodel)
    uic.setup()

    # start stock index price updater
    sifupdter = SIFPriceUpdater(p, sindexmodel, jsd_sessioncfg, uic)
    sifupdter.start()

    # start SIFOrderPushee
    sifop = SIFOrderPushee(p, sindexmodel, jsd_sessioncfg)
    sifop.start()

    # start base diff updater
    bdiffupdter = basediffUpdater(shdbfn, shmapfn, jsd_sessioncfg, uic)
    bdiffupdter.start()

    window.show()
    app.exec_()

    # exit process
    logger.info("waiting basediffUpdater to stop")
    bdiffupdter.stop()
    bdiffupdter.join()

    logger.info("waiting SIFPriceUpdater to stop")
    sifupdter.stop()
    sifupdter.join()

    logger.info("waiting SIFOrderPushee to stop")
    sifop.stop()
    sifop.join()

    logger.info("notify updater threads to stop.")
    pupdater.stop()
    orderupdater.stop()
    logger.info("waiting updater threads to stop.")
    pupdater.join()
    orderupdater.join()
    logger.info("updater threads stopped.")
    logger.info("waiting jzWorkers to finalize jobs")
    # next line ensures all async request will be executed before exit.
    tqueue.join()
    for i in range(jzWorkerNum):
        workers[i].stop()
    for i in range(jzWorkerNum):
        workers[i].join()
    logger.info("jzWorkers stopped")
    logger.info("saving order info.")
    p.savePortfolio()
    p.close()
    pupdater.close()
    orderupdater.close()
    logger.info("I will exit.")

if __name__=="__main__":
    main(sys.argv)

