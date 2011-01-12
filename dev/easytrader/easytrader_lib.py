# -*- coding: utf-8 -*-

import os, sys
import csv
import zlib
import glob
import random
import socket
import pickle
import Queue
import ConfigParser
#from mx import Queue
import cProfile
from threading import Thread, currentThread, Lock, Event
from binascii import unhexlify
from struct import pack, unpack
import time
from datetime import datetime, date, timedelta
import types
from ctypes import *
import logging, logging.config
import sqlite3 as db
import asyncore

import util
import jz, jsd
import jsdhq
from dbfpy import dbf
from PyQt4 import Qt
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.phonon import *
import tradeui
from stockquery import stockquerydlg
from positioninfo import positioninfodlg
from jzworker_ac import jzworker_ac

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

        rowkey = self.portfolio.stocklist[index.row()]
        columnkey = self.portfolio.stockmodelattr[index.column()]
        if role == Qt.DisplayRole:
            try:
                rawdata = self.portfolio.stockinfo[rowkey][columnkey]
                if not isinstance(rawdata, unicode):# expect rawdata as numbers here
                    rawdata = str(rawdata)
                celldata = QString(rawdata)
                return QVariant(celldata)
            except KeyError:
                if columnkey == "state":
                    # "state" is special, it's not a real key in si
                    # but virtual. It represent the state of last
                    # operation on a stock.
                    si = self.portfolio.stockinfo[rowkey]
                    rawdata = ""
                    if len(si["pastsell"]) > 0:
                        rawdata = si["pastsell"][-1]["order_state"]
                    elif len(si["pastbuy"]) > 0:
                        rawdata = si["pastbuy"][-1]["order_state"]
                    if rawdata != "":
                        rawdata = self.portfolio.stockstatemap[rawdata]
                    return QVariant(QString(rawdata))
        elif role == Qt.BackgroundRole:
            si = self.portfolio.stockinfo[rowkey]
            try:
                if si["stopped"] == True:
                    return QVariant(QColor(Qt.gray))
            except KeyError:
                pass

            if columnkey == "state":
                orec = None
                if len(si["pastsell"]) != 0:
                    orec = si["pastsell"][-1]
                elif len(si["pastbuy"]) != 0:
                    orec = si["pastbuy"][-1]

                if orec:
                    if orec["order_state"] in (Portfolio.BUYFAILED, Portfolio.CANCELBUYFAILED,
                            Portfolio.SELLFAILED, Portfolio.CANCELSELLFAILED):
                        return QVariant(QColor(Qt.red))
                    elif orec["order_state"] in (Portfolio.CANCELBUYWAIT,
                            Portfolio.CANCELSELLWAIT):
                        return QVariant(QColor(Qt.yellow))
                    else:
                        if orec["dealcount"] != orec["ordercount"]:
                            return QVariant(QColor(Qt.green))

        return QVariant()

    @pyqtSlot(int)
    def updaterow(self, rowindex):
        self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                self.index(rowindex,0),
                self.index(rowindex, len(self.portfolio.stockmodelattr)-1))

    @pyqtSlot()
    def updateall(self):
        self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                self.index(0,0),
                self.index(len(self.portfolio.stocklist)-1, len(self.portfolio.stockmodelattr)-1))

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
            if isinstance(rawdata, float):
                rawdata = "%0.2f" % rawdata
            elif not isinstance(rawdata, unicode):# expect rawdata as numbers here
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
        self.data["code"] = ""
        #self.data["order_state"] = Portfolio.IFUNORDERED
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

    def updatefrom(self, oreq, oresp):
        try:
            resp = oresp.records[0]
            if oresp.anwser == "Y":
                self["order_id"] = resp[1]
                self["order_date"] = str(datetime.today().date())
                self["order_time"] = str(datetime.now().time())
                self["ordercount"] = resp[14]
                self["orderprice"] = resp[15]
                self["longshort"] = oreq["longshort"]
                self["openclose"] = oreq["openclose"]
                self["ifhedge"] = oreq["ifhedge"]
                self["orderseat"] = resp[30]
                self["syscenter"] = resp[19]
            elif oresp.anwser == "N":
                self["order_date"] = str(datetime.today().date())
                self["order_time"] = str(datetime.now().time())
                self["ordercount"] = oreq["count"]
                self["orderprice"] = oreq["price"]
                self["longshort"] = oreq["longshort"]
                self["openclose"] = oreq["openclose"]
                self["ifhedge"] = oreq["ifhedge"]
                self["failcode"] = oresp.failcode
                self["failinfo"] = oresp.failinfo
        except IndexError:
            pass


class PortfolioStat:
    def __init__(self):
        self.data = {}
        self.username = ""
        self.ptfname = ""

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

class PtfStatReporter(Thread):
    """
    report portfolio stats to a remote controller.
    """
    def __init__(self, conn, pstat):
        Thread.__init__(self)
        self.conn = conn
        self.pstat = pstat
        self.runflag = True
        self.logger = logging.getLogger()
        self.name = self.__class__.__name__

    def stop(self):
        self.runflag = False

    def run(self):
        self.logger.info("start running")
        while self.runflag:

            c = util.command()
            c.cmdname = "pstatreport"
            c.args.append(self.pstat.ptfname)
            c.kwargs = self.pstat.data
            self.conn.sendall(c.pack())

            time.sleep(2)

class CmdWorker(Thread):
    """
    receive commands from remote and execute them
    """
    def __init__(self, fconn, uic):
        Thread.__init__(self)
        self.fconn = fconn
        self.uic = uic
        self.runflag = True
        self.logger = logging.getLogger()
        self.name = self.__class__.__name__
        self.btnslotmap = {
                "buyorder":"buyBatch_r",
                "buyorderbatch":"buyBatch2_r",
                "cancelbuyorder":"cancelBuyBatch",
                "saveorder_2":"savePortfolio",
                "opensifbtn":"openshort_r",
                "cancelopensifbtn":"cancelopen",

                "sellorder":"sellBatch_r",
                "sellorderbatch":"sellBatch2_r",
                "cancelsellorder":"cancelSellBatch",
                "saveorder":"savePortfolio",
                "closesifbtn":"closeshort_r",
                "cancelclosesifbtn":"cancelclose",
                }

    def stop(self):
        self.runflag = False

    def run(self):
        self.logger.info("start running")
        while self.runflag:
            try:
                data = self.fconn.read(4)
                (msglen,) = unpack("!I", data)
                cmd = pickle.loads(self.fconn.read(msglen))
            except socket.timeout:
                continue
            except socket.error:
                self.logger.exception("connection error with controller.")
                break

            handler = None
            try:
                handler = getattr(self, cmd.cmdname+"Handler")
                self.logger.info("call %s to process %s",
                        cmd.cmdname+"Handler",
                        str(cmd))
            except AttributeError:
                self.logger.exception("unknown cmd: <%s>", str(cmd))

            try:
                if handler:
                    handler(*cmd.args, **cmd.kwargs)
            except:
                self.logger.exception("handler meets exception")


    def buttonHandler(self, *args, **kwargs):
        # args = buttonname
        slotn = self.btnslotmap[args[0]]
        slot = getattr(self.uic, slotn)
        slot()

    def checkboxHandler(self, *args, **kwargs):
        # args = checkboxname, bool state
        chk = getattr(self.uic, args[0])
        QMetaObject.invokeMethod(chk, "setChecked",
                Qt.QueuedConnection,
                Q_ARG("bool", args[1]))

    def doublespinHandler(self, *args, **kwargs):
        # args = spinname, value
        spin = getattr(self.uic, args[0])
        spin.setValue(args[1])

    def comboHandler(self, *args, **kwargs):
        combo = getattr(self.uic, args[0])
        combo.setCurrentIndex(args[1])

    def raiseHandler(self, *args, **kwargs):
        self.uic.activateWindow()
        self.uic.raise_()

class trdClient(Thread):
    """
    the trade client that report portfolio stats to the
    controller, and execute command from controller.

    depends on PtfStatReporter and CmdWorker to work.
    """
    def __init__(self, caddr, cport, pstat, uic):
        Thread.__init__(self)
        self.caddr = caddr
        self.cport = cport
        self.pstat = pstat
        self.uic = uic
        self.runflag = True
        self.logger = logging.getLogger()
        self.name = self.__class__.__name__

    def stop(self):
        self.runflag = False

    def run(self):
        conn = socket.socket()
        try:
            conn.connect((self.caddr, self.cport))
            conn.settimeout(5)
        except socket.error:
            self.logger.warning("cannot connect controller.")
            return

        self.logger.info("connected to controller.")
        self.conn = conn
        self.fconn = conn.makefile("r+b")

        regcmd = util.command()
        regcmd.cmdname = "register"
        regcmd.args = [self.pstat.username, self.pstat.ptfname]
        self.conn.sendall(regcmd.pack())

        psrpter = PtfStatReporter(self.conn, self.pstat)
        cwrker = CmdWorker(self.fconn, self.uic)

        psrpter.start()
        cwrker.start()

        while self.runflag:
            time.sleep(3)

        psrpter.stop()
        cwrker.stop()

        psrpter.join()
        cwrker.join()

        unregcmd = util.command()
        unregcmd.cmdname = "unregister"
        unregcmd.args = [self.pstat.username, self.pstat.ptfname]
        self.conn.sendall(unregcmd.pack())

        self.conn.close()

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
    CANCELBUYWAIT = "CANCELBUYWAIT"
    # next comes sell states
    SELLSUCCESS = "SELLSUCCESS"
    SELLFAILED = "SELLFAILED"
    CANCELSELLSUCCESS = "CANCELSELLSUCCESS"
    CANCELSELLFAILED = "CANCELSELLFAILED"
    CANCELSELLWAIT = "CANCELSELLWAIT"

    stockstatemap = {
            INVALID:u"非法",
            UNORDERED:u"未委托",
            # first is buy states,
            BUYSUCCESS:u"买入成功",
            BUYFAILED:u"买入失败",
            # assumption: only success order can be canceled,
            CANCELBUYSUCCESS:u"撤买成功",
            CANCELBUYFAILED:u"撤买失败",
            CANCELBUYWAIT:u"撤买等成交",
            # next comes sell states,
            SELLSUCCESS:u"卖出成功",
            SELLFAILED:u"卖出失败",
            CANCELSELLSUCCESS:u"撤卖成功",
            CANCELSELLFAILED:u"撤卖失败",
            CANCELSELLWAIT:u"撤卖等成交"
            }

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
        self.logfn = ""
        self.logger = logging.getLogger()
        if not self.session.setup():
            self.logger.warning("session setup failed.")
            self.close()
        self.tqueue = tqueue
        self.bolock = Lock()
        self.sindexlock = Lock()

        self.updtlock = updtlock

        self.forcecancelbuy = False
        self.forcecancelsell = False

        # define stock data and buy/sell records attributes
        self.stocklist = []
        self.orderlist = []
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
                "stopped",
                # of type utf8 string
                "state"]
        self.buypricefix = 0.00
        self.sellpricefix = 0.00

        # use market+stock number as key, dict of dict
        self.stockinfo = {}

        # TODO: model attributes
        self.stockmodelattr = ["count", "market", "code", "name",
                #"order_state", "ordercount", "dealcount", "orderprice",
                #"dealprice", "latestprice", "order_date", "order_time",
                "close", "open",
                "latestprice", "ceiling", "floor",
                "tobuyprice", "tosellprice",
                "currentbuycount", "currentbuycost",
                "currentsellcount", "currentsellgain",
                "state"]
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
                "currentsellgain":u"卖出获利",
                "state":u"操作状态",
                "ceiling":u"涨停",
                "floor":u"跌停"
                }
        # price policies
        self.pricepolicylist = ["latest", "s5", "s4", "s3", "s2", "s1", "b1", "b2", "b3", "b4", "b5"]
        self.buypolicy = "latest"
        self.sellpolicy = "latest"
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
                "b5":u"买五",
                "mktval":u"市价"
                }

        self._bostate = Portfolio.BOUNORDERED

        self.sindexattr = ["count", "code",
                # of type float
                "latestprice", "open", "close", "ceiling", "floor",
                # of type float
                "openposprice", "closeposprice",
                # of type SIndexRecord
                "pastopen", "pastclose",
                # of type float
                "opencount", "closecount", "earning",
                "openavg", "closeavg",
                # of dict order_id -> (dealcount, dealprice)
                "deals",
                "stopped", "state"]
        self.sindexmodelattr = ["count", "code",
                "latestprice", "close", "open", "ceiling", "floor",
                "openposprice", "closeposprice",
                "opencount", "closecount", "earning",
                "openavg", "closeavg",
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
                "openavg":u"开仓均价",
                "closeavg":u"平仓均价",
                "openposprice":u"欲开仓价",
                "closeposprice":u"欲平仓价",
                "stopped":u"停牌",
                "opencount":u"建仓量",
                "closecount":u"平仓量",
                "earning":u"盈亏",
                "state":u"状态"
                }
        self.sindexinfo = {}
        self.sindexpricepolicylist = ["mktval", "latest", "s1", "b1", ]
        self.openpolicy = "mktval"
        self.closepolicy = "mktval"
        self.openpricefix = 0.0
        self.closepricefix = 0.0
        self.jsdcfg = jsdcfg
        s = jsd.session(self.jsdcfg)
        if not s.setup():
            self.logger.warning("Cannot login into jsd")
            #self.close()
        self.jsdsession = s

        # order id for the last order in quick sif operation
        self.sifquickinfo = SIndexRecord()

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
        if self.session:
            self.session.close()
            self.session = None

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
                self.sindexinfo["deals"] = {}
                try:
                    self.sindexinfo["deals"] = eval(i[6])
                except IndexError:
                    pass
                self.updateopencount()
                self.updateclosecount()
                self.updateearning()
                # TODO: update opencount, closecount, earning
                # TODO: also save deals in savePortfolio
            else:# stock batch
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
            #self.logger.info("saving portfolio")
            if ptfn == None:
                f = open(self.ptfn, "wb")
            else:
                f = open(ptfn, "wb")
            writer = csv.writer(f)

            # write IF first
            try:
                writer.writerow(["IF", self.sindexinfo["code"], self.sindexinfo["count"],
                    self.sindexinfo["state"].encode("utf-8"), self.sindexinfo["pastopen"],
                    self.sindexinfo["pastclose"], self.sindexinfo["deals"]])
            except KeyError:# no sif info
                pass
            for scode in self.stocklist:
                si = self.stockinfo[scode]
                writer.writerow([si["market"], si["code"],
                    si["count"],
                    repr(si["pastbuy"]),
                    repr(si["pastsell"])])
            # portfolio state as a batch
            writer.writerow(["BO", self.bostate.encode("utf-8")])
            f.flush()
            f.close()
            #self.logger.info("saved")

    def isvalidbuy(self, si, scode):
        if si["stopped"]:
            return False
        if int(si["count"]) - si["pastbuycount"] < 50:
            return False
        if si["tobuyprice"] > si["ceiling"] or si["tobuyprice"] < si["floor"]:
            return False
        if si["tobuyprice"] == 0:
            return False
        return True

    def isvalidsell(self, si, scode):
        if si["stopped"]:
            return False
        if si["pastbuycount"] - si["pastsellcount"] <= 0:
            return False
        if si["tosellprice"] > si["ceiling"] or si["tosellprice"] < si["floor"]:
            return False
        if si["tosellprice"] == 0:
            return False
        return True

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
            for scode in self.orderlist:
                si = self.stockinfo[scode]
                if not self.isvalidbuy(si, scode):
                    continue

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
                orec["orderprice"] = "%0.2f" % si["tobuyprice"]
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
                self.logger.info("no stock to buy.")
                self.bostate = Portfolio.BOUNORDERED
            else:
                self.logger.info("buy batch dispatched: %d" % self.bocount)
            #assert len(self.stockinfo) == self.bocount
            # assert not true on stopped stocks

        elif self.bostate == Portfolio.BOBUYCANCELED:
            # re-buy: only buy stock in CANCELBUYSUCCESS state
            self.bostate = Portfolio.BOBUYING
            self.bocount = 0

            reqclass = jz.SubmitOrderReq
            respclass = jz.SubmitOrderResp
            trdcode = "0B"
            for scode in self.orderlist:
                si = self.stockinfo[scode]
                if not self.isvalidbuy(si, scode):
                    continue

                # there's case that a stock is never ordered, e.g. stopped yestoday.
                if len(si["pastbuy"]) == 0 or si["pastbuy"][-1]["order_state"] == Portfolio.CANCELBUYSUCCESS:
                    self.bocount = self.bocount + 1

                    orec = OrderRecord()
                    orec["order_state"] = Portfolio.UNORDERED
                    orec["ordercount"] = str( round100(int(si["count"]) - si["pastbuycount"]) )
                    orec["orderprice"] = "%0.2f" % si["tobuyprice"]
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
                self.logger.info("buy batch dispatched: %d" % self.bocount)

        elif self.bostate == Portfolio.BOBUYSUCCESS:
            self.bostate = Portfolio.BOBUYING
            self.bocount = 0

            reqclass = jz.SubmitOrderReq
            respclass = jz.SubmitOrderResp
            trdcode = "0B"
            for scode in self.orderlist:
                si = self.stockinfo[scode]
                if not self.isvalidbuy(si, scode):
                    continue

                # only buy fresh stocks, e.g. recovered from stop.
                if len(si["pastbuy"]) == 0 or si["pastbuy"][-1]["order_state"] == Portfolio.CANCELBUYSUCCESS:
                    self.bocount = self.bocount + 1

                    orec = OrderRecord()
                    orec["order_state"] = Portfolio.UNORDERED
                    orec["ordercount"] = str( round100(int(si["count"]) - si["pastbuycount"]) )
                    orec["orderprice"] = "%0.2f" % si["tobuyprice"]
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
                self.bostate = Portfolio.BOBUYSUCCESS

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
        if self.bocount == 0:
            self.savePortfolio()

    def buyBatch2Top(self):
        self.bolock.acquire()
        self.logger.info("batch buying with batch interface")

        self.bocount = 0
        self.boerror = False
        tobuy = []

        if self.bostate == Portfolio.BOUNORDERED:
            # new and first batch buy order
            for scode in self.orderlist:
                si = self.stockinfo[scode]
                if not self.isvalidbuy(si, scode):
                    continue

                try:
                    assert si["pastbuy"] == []
                    assert si["pastsell"] == []
                    assert si["pastbuycount"] == 0
                    assert si["pastbuycost"] == 0.0
                    assert si["pastsellcount"] == 0
                    assert si["pastsellgain"] == 0.0
                except AssertionError:
                    continue

                self.bocount = self.bocount + 1
                tobuy.append(scode)

        elif self.bostate == Portfolio.BOBUYCANCELED:
            # re-buy: only buy stock in CANCELBUYSUCCESS state
            for scode in self.orderlist:
                si = self.stockinfo[scode]
                if not self.isvalidbuy(si, scode):
                    continue

                # there's case that a stock is never ordered, e.g. stopped yestoday.
                if len(si["pastbuy"]) == 0 or si["pastbuy"][-1]["order_state"] == Portfolio.CANCELBUYSUCCESS:
                    self.bocount = self.bocount + 1
                    tobuy.append(scode)

        elif self.bostate == Portfolio.BOBUYSUCCESS:
            for scode in self.orderlist:
                si = self.stockinfo[scode]
                if not self.isvalidbuy(si, scode):
                    continue

                # only buy fresh stocks, e.g. recovered from stop.
                if len(si["pastbuy"]) == 0 or si["pastbuy"][-1]["order_state"] == Portfolio.CANCELBUYSUCCESS:
                    self.bocount = self.bocount + 1
                    tobuy.append(scode)

        else:
            self.logger.info("not in buy-able state")

        if self.bocount == 0:
            self.logger.info("no stock to buy.")
        else:
            self.bostate = Portfolio.BOBUYING
            tobuysh = []
            tobuysz = []
            for scode in tobuy:
                si = self.stockinfo[scode]

                orec = OrderRecord()
                orec["order_state"] = Portfolio.UNORDERED
                orec["ordercount"] = str( round100(int(si["count"]) - si["pastbuycount"]) )
                orec["orderprice"] = "%0.2f" % si["tobuyprice"]
                si["pastbuy"].append(orec)

                if si["market"] == "SH":
                    tobuysh.append( [si["code"], orec["orderprice"], orec["ordercount"]] )
                elif si["market"] == "SZ":
                    tobuysz.append( [si["code"], orec["orderprice"], orec["ordercount"]] )

            reqclass = jz.BatchOrderReq
            respclass = jz.BatchOrderResp
            batchnum = 50
            for i in range(0, len(tobuysh), batchnum):
                param = {}
                param["account"] = self.session["account"]
                param["customer"] = self.session["user_code"]
                param["market"] = jz.SHAMARKET
                param["board"] = "0"
                param["secu_acc"] = self.session["secu_acc"]["SH"]
                param["trd_id"] = "0B"
                param["stocklist"] = tobuysh[i:i+batchnum]
                param["price_msg"] = reqclass.genorder(param["stocklist"])
                self.tqueue.put( (reqclass, respclass, param, self.buyBatch2Bottom, True) )

            for i in range(0, len(tobuysz), batchnum):
                param = {}
                param["account"] = self.session["account"]
                param["customer"] = self.session["user_code"]
                param["market"] = jz.SZAMARKET
                param["board"] = "0"
                param["secu_acc"] = self.session["secu_acc"]["SZ"]
                param["trd_id"] = "0B"
                param["stocklist"] = tobuysz[i:i+batchnum]
                param["price_msg"] = reqclass.genorder(param["stocklist"])
                self.tqueue.put( (reqclass, respclass, param, self.buyBatch2Bottom, True) )

        self.bolock.release()

    buyBatch2 = buyBatch2Top

    def buyBatch2Bottom(self, req, resp, param):
        today = str(datetime.today().date())
        mkt = ""
        if param["market"] == "10":
            mkt = "SH"
        elif param["market"] == "00":
            mkt = "SZ"
        assert mkt != ""

        self.bolock.acquire()
        if resp.retcode == "0":
            for r in resp.records:
                self.bocount = self.bocount - 1
                scode = mkt + r[1]
                orec = self.stockinfo[scode]["pastbuy"][-1]
                orec["order_state"] = Portfolio.BUYSUCCESS
                orec["order_date"] = today
                orec["order_time"] = str(datetime.now().time())
                orec["order_id"] = r[0]
        else:
            self.logger.warning("batch order failed %s:%s" % (resp.retcode, resp.retinfo))
            self.boerror = True
            for s in param["stocklist"]:
                self.bocount = self.bocount - 1
                scode = mkt + s[0]
                orec = self.stockinfo[scode]["pastbuy"][-1]
                orec["order_state"] = Portfolio.CANCELBUYSUCCESS

        if self.bocount == 0:
            self.bostate = Portfolio.BOBUYSUCCESS
            self.logger.info("batch buy-ed")
            if self.boerror:
                QMetaObject.invokeMethod(self.uic,
                        "warnbatchfailed", Qt.QueuedConnection)
        self.bolock.release()
        if self.bocount == 0:
            self.savePortfolio()

    def cancelBuyBatchTop(self):
        self.bolock.acquire()
        self.logger.info("batch buy canceling")

        if self.bostate in (Portfolio.BOBUYSUCCESS, Portfolio.BOBUYCANCELED):
            # set Portfolio batch state
            oldbostate = self.bostate
            self.bostate = Portfolio.BOBUYCANCELING
            self.bocount = 0

            # submit each stock order
            reqclass = jz.CancelOrderReq
            respclass = jz.CancelOrderResp

            # block update to ALL orders
            self.updtlock.acquire()

            for scode in self.orderlist:
                # only cancel (BUYSUCCESS and dealcount < ordercount) orders
                si = self.stockinfo[scode]
                try:
                    orec = si["pastbuy"][-1]
                except IndexError:
                    continue

                if orec["order_state"] == Portfolio.BUYSUCCESS and int(orec["dealcount"]) < int(orec["ordercount"]):
                    # cancel if latestprice is going up
                    if self.forcecancelbuy or float(orec["orderprice"]) < si["latestprice"]:
                        today = datetime.today().replace(hour=9,minute=0,second=0,microsecond=0)
                        odate = datetime.strptime(orec["order_date"], "%Y-%m-%d")
                        # note: omit microseconds part
                        otime = datetime.strptime(orec["order_time"].split(".")[0], "%H:%M:%S").time()
                        odatetime = datetime.combine(odate, otime)
                        # orders older than today is canceled at local directly
                        if odatetime < today:
                            orec["cancel_date"] = str(today.date())
                            orec["cancel_time"] = str(datetime.now().time())
                            orec["order_state"] = Portfolio.CANCELBUYSUCCESS
                        else:
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
                self.bostate = oldbostate
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
        orec["cancel_date"] = today
        orec["cancel_time"] = str(datetime.now().time())
        if resp.retcode in ("0", "409"):
            orec["order_state"] = Portfolio.CANCELBUYWAIT
        else:
            orec["order_state"] = Portfolio.CANCELBUYFAILED

        # update stock info immediately, it's important to use req.session,
        # not self.session, to make sure sqlite db object is used by
        # only one thread
        if orec["order_state"] == Portfolio.CANCELBUYWAIT:
            needmore = True
            trycount = 0
            maxtrycount = 0
            ordercount = int(orec["ordercount"])
            while needmore and trycount < maxtrycount:
                trycount += 1
                qoreq = jz.QueryOrderReq(req.session)
                qoreq["begin_date"] = orec["order_date"]
                qoreq["end_date"] = orec["order_date"]
                qoreq["get_orders_mode"] = "0" # all submissions
                qoreq["user_code"] = req.session["user_code"]
                # a bug in protocol/document results in next odd line
                qoreq["biz_no"] = orec["order_id"]
                time.sleep(0.1)
                qoreq.send()
                qoresp = jz.QueryOrderResp(req.session)
                qoresp.recv()
                if qoresp.retcode == "0":
                    wdqty, dealcount, dealamount, dealprice = qoresp.getTotal()
                    if dealcount != None and (wdqty+dealcount==ordercount):
                        needmore = False
                        orec["dealcount"] = str(dealcount)
                        orec["dealamount"] = str(dealamount)
                        orec["dealprice"] = str(dealprice)
                        if orec["dealcount"] == orec["ordercount"]:
                            orec["order_state"] = Portfolio.BUYSUCCESS
                        else:
                            orec["order_state"] = Portfolio.CANCELBUYSUCCESS
                    elif trycount >= maxtrycount:
                            orec["order_state"] = Portfolio.CANCELBUYWAIT
                            #self.logger.error("cancel waiting: %s" % scode)
                else:
                    self.logger.error("error when update order for %s (%s:%s)",
                            orec["order_id"], qoresp.retcode, qoresp.retinfo)

            #self.logger.info("tried %d time query order @cancel" % trycount)
            #if trycount >= maxtrycount:
            #    self.logger.warning("tried more than %d times.", maxtrycount)

            # update pastbuyxxx
            if orec["order_state"] in (Portfolio.BUYSUCCESS, Portfolio.CANCELBUYSUCCESS):
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
        if self.bocount == 0:
            self.savePortfolio()

    def sellBatchTop(self):
        self.bolock.acquire()
        self.logger.info("batch selling")

        if self.bostate == Portfolio.BOBUYSUCCESS:
            # only succeed when all buysuccess stocks are 100% buyed
            allbought = True
            for scode in self.orderlist:
                si = self.stockinfo[scode]
                try:
                    orec = si["pastbuy"][-1]
                except IndexError:
                    continue

                assert si["pastsell"] == []
                assert si["pastsellcount"] == 0
                if orec["order_state"] == Portfolio.BUYSUCCESS:
                    if orec["ordercount"] != orec["dealcount"]:
                        self.logger.info("stock %s is in buying, cancel order fist and then sell." % scode)
                        QMessageBox.warning(None,
                                u"",
                                u"<FONT COLOR='#FF0000'>%s尚未撤买</FONT>"%scode,
                                QMessageBox.Ok)
                        allbought = False
                        break
                    else:
                        try:
                            assert int(si["count"]) == si["pastbuycount"]# + int(orec["dealcount"])
                        except AssertionError:
                            self.logger.warning("total buy is not equal to expected, %s, %s:%d",
                                    scode, si["count"], si["pastbuycount"])
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
            for scode in self.orderlist:
                si = self.stockinfo[scode]
                if not self.isvalidsell(si, scode):
                    continue

                try:
                    orec = si["pastbuy"][-1]
                except IndexError:
                    continue

                if orec["order_state"] == Portfolio.BUYSUCCESS:
                    # DO sell
                    self.bocount = self.bocount + 1
                    orec = OrderRecord()
                    orec["order_state"] = Portfolio.UNORDERED
                    orec["ordercount"] = str( si["pastbuycount"] - si["pastsellcount"] )
                    orec["orderprice"] = "%0.2f" % si["tosellprice"]
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
            allbought = True
            for scode in self.orderlist:
                si = self.stockinfo[scode]
                assert si["pastsell"] == []
                assert si["pastsellcount"] == 0

                try:
                    orec = si["pastbuy"][-1]
                except IndexError:
                    continue

                if orec["order_state"] == Portfolio.BUYSUCCESS:
                    if orec["ordercount"] != orec["dealcount"]:
                        self.logger.info("stock %s is in buying, cancel order fist and then sell." % scode)
                        QMessageBox.warning(None,
                                u"",
                                u"<FONT COLOR='#FF0000'>%s尚未撤买</FONT>"%scode,
                                QMessageBox.Ok)
                        allbought = False
                        break
                    else:
                        try:
                            assert int(si["count"]) == si["pastbuycount"]# + int(orec["dealcount"])
                        except AssertionError:
                            self.logger.warning("total buy is not equal to expected, %s, %s:%d",
                                    scode, si["count"], si["pastbuycount"])
                    # only update pastbuyxxx for BUYSECCESS stocks
                    # NOTE: code is not necessary
                    #assert int(si["count"]) == si["pastbuycount"] + int(orec["dealcount"])
                    #si["pastbuycount"] = si["pastbuycount"] + int(orec["dealcount"])
                    #si["pastbuycost"] = si["pastbuycost"] + float(orec["dealamount"])
                elif orec["order_state"] == Portfolio.CANCELBUYSUCCESS:
                    pass
                    #assert int(orec["ordercount"]) > int(orec["dealcount"])
                    # pastbuycount is updated in cancelBuyBatchBottom for this case
            if allbought == False:
                self.bolock.release()
                return

            # Now we sell stocks
            reqclass = jz.SubmitOrderReq
            respclass = jz.SubmitOrderResp
            trdcode = "0S"
            self.bostate = Portfolio.BOSELLING
            self.bocount = 0
            for scode in self.orderlist:
                si = self.stockinfo[scode]
                if not self.isvalidsell(si, scode):
                    continue

                try:
                    orec = si["pastbuy"][-1]
                except IndexError:
                    continue

                if orec["order_state"] in (Portfolio.BUYSUCCESS, Portfolio.CANCELBUYSUCCESS):
                    # DO sell
                    self.bocount = self.bocount + 1
                    orec = OrderRecord()
                    orec["order_state"] = Portfolio.UNORDERED
                    orec["ordercount"] = str( si["pastbuycount"] - si["pastsellcount"] )
                    orec["orderprice"] = "%0.2f" % si["tosellprice"]
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
            for scode in self.orderlist:
                si = self.stockinfo[scode]
                if not self.isvalidsell(si, scode):
                    continue

                if len(si["pastsell"]) == 0 or si["pastsell"][-1]["order_state"] == Portfolio.CANCELSELLSUCCESS:
                    # DO sell
                    self.bocount = self.bocount + 1
                    orec = OrderRecord()
                    orec["order_state"] = Portfolio.UNORDERED
                    orec["ordercount"] = str( si["pastbuycount"] - si["pastsellcount"] )
                    orec["orderprice"] = "%0.2f" % si["tosellprice"]
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

        elif self.bostate == Portfolio.BOSELLSUCCESS:
            # At this point, pastsellxxx should be updated correctly.
            reqclass = jz.SubmitOrderReq
            respclass = jz.SubmitOrderResp
            trdcode = "0S"
            self.bostate = Portfolio.BOSELLING
            self.bocount = 0
            for scode in self.orderlist:
                si = self.stockinfo[scode]
                if not self.isvalidsell(si, scode):
                    continue

                if len(si["pastsell"]) == 0 or si["pastsell"][-1]["order_state"] == Portfolio.CANCELSELLSUCCESS:
                    # DO sell
                    self.bocount = self.bocount + 1
                    orec = OrderRecord()
                    orec["order_state"] = Portfolio.UNORDERED
                    orec["ordercount"] = str( si["pastbuycount"] - si["pastsellcount"] )
                    orec["orderprice"] = "%0.2f" % si["tosellprice"]
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
                self.bostate = Portfolio.BOSELLSUCCESS

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
        if self.bocount == 0:
            self.savePortfolio()

    def sellBatch2Top(self):
        self.bolock.acquire()
        self.logger.info("batch selling with batch interface")

        self.bocount = 0
        self.boerror = False
        tosell = []

        if self.bostate == Portfolio.BOBUYSUCCESS:
            # only succeed when all buysuccess stocks are 100% buyed
            allbought = True
            for scode in self.orderlist:
                si = self.stockinfo[scode]
                try:
                    orec = si["pastbuy"][-1]
                except IndexError:
                    continue

                assert si["pastsell"] == []
                assert si["pastsellcount"] == 0
                if orec["order_state"] == Portfolio.BUYSUCCESS:
                    if orec["ordercount"] != orec["dealcount"]:
                        self.logger.info("stock %s is in buying, cancel order fist and then sell." % scode)
                        QMessageBox.warning(None,
                                u"",
                                u"<FONT COLOR='#FF0000'>%s尚未撤买</FONT>"%scode,
                                QMessageBox.Ok)
                        allbought = False
                        break
                    else:
                        try:
                            assert int(si["count"]) == si["pastbuycount"]# + int(orec["dealcount"])
                        except AssertionError:
                            self.logger.warning("total buy is not equal to expected, %s, %s:%d",
                                    scode, si["count"], si["pastbuycount"])
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
            for scode in self.orderlist:
                si = self.stockinfo[scode]
                if not self.isvalidsell(si, scode):
                    continue

                try:
                    orec = si["pastbuy"][-1]
                except IndexError:
                    continue

                if orec["order_state"] == Portfolio.BUYSUCCESS:
                    # DO sell
                    self.bocount = self.bocount + 1
                    tosell.append(scode)

        elif self.bostate == Portfolio.BOBUYCANCELED:
            # sell stocks in CANCELBUYSUCCESS state and (BUYSUCCESS and 100% buy) state.
            # At this point, stock in BUYSUCCESS state should be bought completely.
            # first is some sanity check, and updating pastbuyxxx for BUYSUCCESS stocks
            allbought = True
            for scode in self.orderlist:
                si = self.stockinfo[scode]
                assert si["pastsell"] == []
                assert si["pastsellcount"] == 0

                try:
                    orec = si["pastbuy"][-1]
                except IndexError:
                    continue

                if orec["order_state"] == Portfolio.BUYSUCCESS:
                    if orec["ordercount"] != orec["dealcount"]:
                        self.logger.info("stock %s is in buying, cancel order fist and then sell." % scode)
                        QMessageBox.warning(None,
                                u"",
                                u"<FONT COLOR='#FF0000'>%s尚未撤买</FONT>"%scode,
                                QMessageBox.Ok)
                        allbought = False
                        break
                    else:
                        try:
                            assert int(si["count"]) == si["pastbuycount"]# + int(orec["dealcount"])
                        except AssertionError:
                            self.logger.warning("total buy is not equal to expected, %s, %s:%d",
                                    scode, si["count"], si["pastbuycount"])
                    # only update pastbuyxxx for BUYSECCESS stocks
                    # NOTE: code is not necessary
                    #assert int(si["count"]) == si["pastbuycount"] + int(orec["dealcount"])
                    #si["pastbuycount"] = si["pastbuycount"] + int(orec["dealcount"])
                    #si["pastbuycost"] = si["pastbuycost"] + float(orec["dealamount"])
                elif orec["order_state"] == Portfolio.CANCELBUYSUCCESS:
                    pass
                    #assert int(orec["ordercount"]) > int(orec["dealcount"])
                    # pastbuycount is updated in cancelBuyBatchBottom for this case
            if allbought == False:
                self.bolock.release()
                return

            # Now we sell stocks
            for scode in self.orderlist:
                si = self.stockinfo[scode]
                if not self.isvalidsell(si, scode):
                    continue

                try:
                    orec = si["pastbuy"][-1]
                except IndexError:
                    continue

                if orec["order_state"] in (Portfolio.BUYSUCCESS, Portfolio.CANCELBUYSUCCESS):
                    # DO sell
                    self.bocount = self.bocount + 1
                    tosell.append(scode)

        elif self.bostate == Portfolio.BOSELLCANCELED:
            # At this point, pastsellxxx should be updated correctly.
            for scode in self.orderlist:
                si = self.stockinfo[scode]
                if not self.isvalidsell(si, scode):
                    continue

                if len(si["pastsell"]) == 0 or si["pastsell"][-1]["order_state"] == Portfolio.CANCELSELLSUCCESS:
                    # DO sell
                    self.bocount = self.bocount + 1
                    tosell.append(scode)

        elif self.bostate == Portfolio.BOSELLSUCCESS:
            # At this point, pastsellxxx should be updated correctly.
            for scode in self.orderlist:
                si = self.stockinfo[scode]
                if not self.isvalidsell(si, scode):
                    continue

                if len(si["pastsell"]) == 0 or si["pastsell"][-1]["order_state"] == Portfolio.CANCELSELLSUCCESS:
                    # DO sell
                    self.bocount = self.bocount + 1
                    tosell.append(scode)

        else:
            self.logger.info("not in sell-able state")

        if self.bocount == 0:
            self.logger.info("no stock to sell")
        else:
            self.bostate = Portfolio.BOSELLING
            tosellsh = []
            tosellsz = []
            for scode in tosell:
                si = self.stockinfo[scode]

                orec = OrderRecord()
                orec["order_state"] = Portfolio.UNORDERED
                orec["ordercount"] = str( si["pastbuycount"] - si["pastsellcount"] )
                orec["orderprice"] = "%0.2f" % si["tosellprice"]
                si["pastsell"].append(orec)

                if si["market"] == "SH":
                    tosellsh.append( [si["code"], orec["orderprice"], orec["ordercount"]] )
                elif si["market"] == "SZ":
                    tosellsz.append( [si["code"], orec["orderprice"], orec["ordercount"]] )

            reqclass = jz.BatchOrderReq
            respclass = jz.BatchOrderResp
            batchnum = 50
            for i in range(0, len(tosellsh), batchnum):
                param = {}
                param["account"] = self.session["account"]
                param["customer"] = self.session["user_code"]
                param["market"] = jz.SHAMARKET
                param["board"] = "0"
                param["secu_acc"] = self.session["secu_acc"]["SH"]
                param["trd_id"] = "0S"
                param["stocklist"] = tosellsh[i:i+batchnum]
                param["price_msg"] = reqclass.genorder(param["stocklist"])
                self.tqueue.put( (reqclass, respclass, param, self.sellBatch2Bottom, True) )

            for i in range(0, len(tosellsz), batchnum):
                param = {}
                param["account"] = self.session["account"]
                param["customer"] = self.session["user_code"]
                param["market"] = jz.SZAMARKET
                param["board"] = "0"
                param["secu_acc"] = self.session["secu_acc"]["SZ"]
                param["trd_id"] = "0S"
                param["stocklist"] = tosellsz[i:i+batchnum]
                param["price_msg"] = reqclass.genorder(param["stocklist"])
                self.tqueue.put( (reqclass, respclass, param, self.sellBatch2Bottom, True) )

        self.bolock.release()

    sellBatch2 = sellBatch2Top

    def sellBatch2Bottom(self, req, resp, param):
        today = str(datetime.today().date())
        mkt = ""
        if param["market"] == "10":
            mkt = "SH"
        elif param["market"] == "00":
            mkt = "SZ"
        assert mkt != ""

        self.bolock.acquire()
        if resp.retcode == "0":
            for r in resp.records:
                self.bocount = self.bocount - 1
                scode = mkt + r[1]
                orec = self.stockinfo[scode]["pastsell"][-1]
                orec["order_state"] = Portfolio.SELLSUCCESS
                orec["order_date"] = today
                orec["order_time"] = str(datetime.now().time())
                orec["order_id"] = r[0]
        else:
            self.logger.warning("batch order failed %s:%s" % (resp.retcode, resp.retinfo))
            self.boerror = True
            for s in param["stocklist"]:
                self.bocount = self.bocount - 1
                scode = mkt + s[0]
                orec = self.stockinfo[scode]["pastsell"][-1]
                orec["order_state"] = Portfolio.CANCELSELLSUCCESS

        if self.bocount == 0:
            self.bostate = Portfolio.BOSELLSUCCESS
            self.logger.info("batch selled")
            if self.boerror:
                QMetaObject.invokeMethod(self.uic,
                        "warnbatchfailed", Qt.QueuedConnection)
        self.bolock.release()
        if self.bocount == 0:
            self.savePortfolio()

    def cancelSellBatchTop(self):
        self.bolock.acquire()
        self.logger.info("batch sell canceling")

        if self.bostate in (Portfolio.BOSELLSUCCESS, Portfolio.BOSELLCANCELED):
            oldbostate = self.bostate
            self.bostate = Portfolio.BOSELLCANCELING
            self.bocount = 0

            reqclass = jz.CancelOrderReq
            respclass = jz.CancelOrderResp

            # block update to ALL orders
            self.updtlock.acquire()

            for scode in self.orderlist:
                # only cancel (SELLSUCCESS and dealcount < ordercount) orders
                si = self.stockinfo[scode]
                try:
                    orec = si["pastsell"][-1]
                except IndexError:
                    continue

                if orec["order_state"] == Portfolio.SELLSUCCESS and int(orec["dealcount"]) < int(orec["ordercount"]):
                    # cancel if latestprice is going down
                    if self.forcecancelsell or float(orec["orderprice"]) > si["latestprice"]:
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
                self.bostate = oldbostate
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
        orec["cancel_date"] = today
        orec["cancel_time"] = str(datetime.now().time())
        if resp.retcode in ("0", "409"):
            orec["order_state"] = Portfolio.CANCELSELLWAIT
        else:
            orec["order_state"] = Portfolio.CANCELSELLFAILED

        # update stock info immediately
        if orec["order_state"] == Portfolio.CANCELSELLWAIT:
            needmore = True
            trycount = 0
            maxtrycount = 0
            ordercount = int(orec["ordercount"])
            while needmore and trycount < maxtrycount:
                trycount += 1
                qoreq = jz.QueryOrderReq(req.session)
                qoreq["begin_date"] = orec["order_date"]
                qoreq["end_date"] = orec["order_date"]
                qoreq["get_orders_mode"] = "0" # all submissions
                qoreq["user_code"] = req.session["user_code"]
                # a bug in protocol/document results in next odd line
                qoreq["biz_no"] = orec["order_id"]
                time.sleep(0.1)
                qoreq.send()
                qoresp = jz.QueryOrderResp(req.session)
                qoresp.recv()
                if qoresp.retcode == "0":
                    wdqty, dealcount, dealamount, dealprice = qoresp.getTotal()
                    if dealcount != None and (wdqty+dealcount==ordercount):
                        needmore = False
                        orec["dealcount"] = str(dealcount)
                        orec["dealamount"] = str(dealamount)
                        orec["dealprice"] = str(dealprice)
                        if orec["dealcount"] == orec["ordercount"]:
                            orec["order_state"] = Portfolio.SELLSUCCESS
                        else:
                            orec["order_state"] = Portfolio.CANCELSELLSUCCESS
                    elif trycount >= maxtrycount:
                            orec["order_state"] = Portfolio.CANCELSELLWAIT
                            #self.logger.error("cancel waiting: %s" % scode)
                else:
                    self.logger.error("error when update order for %s (%s:%s)",
                            si["order_id"], qoresp.retcode, qoresp.retinfo)

            #self.logger.info("tried %d time query order @cancel" % trycount)
            #if trycount >= maxtrycount:
            #    self.logger.warning("tried more than %d times.", maxtrycount)

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
        if self.bocount == 0:
            self.savePortfolio()

    def openshort(self):
        with self.sindexlock:
            if self.sindexinfo["state"] in (Portfolio.IFUNORDERED, Portfolio.IFCANCELOPENSHORTOK):
                oreq = jsd.OrderReq(self.jsdsession)
                oreq["exchcode"] = self.jsdsession["cffexcode"]
                oreq["code"] = self.sindexinfo["code"]
                oreq["longshort"] = "1"
                oreq["openclose"] = "0"
                oreq["ifhedge"] = "0"
                opencount = int(self.sindexinfo["count"]) - self.sindexinfo["opencount"]
                if opencount > 0:
                    oreq["count"] = str(opencount)
                    oreq["price"] = "%0.1f" % self.sindexinfo["openposprice"]
                    oreq["clientnum"] = self.jsdsession["clientnum"]
                    oreq["seat"] = self.jsdsession["seat"]
                    oreq.send()
                    sirec = SIndexRecord()
                    self.sindexinfo["pastopen"].append(sirec)
                    oresp = jsd.OrderResp(self.jsdsession)
                    oresp.recv()
                    resp = oresp.records[0]
                    print "orderresp", resp
                    if oresp.anwser == "Y":
                        # NOTE: order state may change after ordering
                        sirec["order_id"] = resp[1]
                        sirec["order_date"] = str(datetime.today().date())
                        sirec["order_time"] = str(datetime.now().time())
                        sirec["ordercount"] = resp[14]
                        sirec["orderprice"] = resp[15]
                        sirec["longshort"] = oreq["longshort"]
                        sirec["openclose"] = oreq["openclose"]
                        sirec["ifhedge"] = oreq["ifhedge"]
                        sirec["orderseat"] = resp[30]
                        sirec["syscenter"] = resp[19]
                        self.sindexinfo["state"] = Portfolio.IFOPENSHORTOK
                        # TODO: test storetrade ok
                    elif oresp.anwser == "N":
                        resp = oresp.records[0]
                        sirec["order_date"] = str(datetime.today().date())
                        sirec["order_time"] = str(datetime.now().time())
                        sirec["ordercount"] = oreq["count"]
                        sirec["orderprice"] = oreq["price"]
                        sirec["longshort"] = oreq["longshort"]
                        sirec["openclose"] = oreq["openclose"]
                        sirec["ifhedge"] = oreq["ifhedge"]
                        self.sindexinfo["state"] = Portfolio.IFOPENSHORTFAILED
                        # TODO: test storetrade ok
                    else:
                        self.logger.warning("unknow order response: %s" % str(oresp.records))

            else:
                self.logger.info("not in open-able state")


    def cancelopenshort(self):
        with self.sindexlock:
            if self.sindexinfo["state"] == Portfolio.IFOPENSHORTOK:
                if self.sindexinfo["opencount"] < int(self.sindexinfo["count"]):
                    si = self.sindexinfo
                    orec = None
                    #if len(si["pastclose"]) != 0:
                    #    orec = si["pastclose"][-1]
                    if len(si["pastopen"]) != 0:
                        orec = si["pastopen"][-1]
                    if orec == None:
                        self.logger.warning("cancel without a previous open.")
                        return

                    coreq = jsd.CancelOrderReq(self.jsdsession)
                    coreq["exchcode"] = self.jsdsession["cffexcode"]
                    coreq["code"] = si["code"]
                    coreq["longshort"] = orec["longshort"]
                    coreq["openclose"] = orec["openclose"]
                    coreq["ifhedge"] = orec["ifhedge"]
                    coreq["count"] = orec["ordercount"]
                    coreq["price"] = orec["orderprice"]
                    coreq["order_id"] = orec["order_id"]
                    coreq["cancelcount"] = str( int(orec["ordercount"]) - si["opencount"] )
                    coreq["syscenter"] = orec["syscenter"]
                    coreq["seat"] = self.jsdsession["seat"]
                    coreq["orderseat"] = orec["orderseat"]
                    coreq.send()
                    coresp = jsd.CancelOrderResp(self.jsdsession)
                    coresp.recv()
                    self.logger.info("cancel open response: %s", str(coresp.records))
                    if coresp.anwser == "Y":
                        self.sindexinfo["state"] = Portfolio.IFCANCELOPENSHORTOK
                    else:
                        # check order state, if order already canceled, or totally
                        # dealed, its state should be ok
                        self.sindexinfo["state"] = Portfolio.IFCANCELOPENSHORTFAILED
                        qoreq = jsd.QueryOrderReq(self.jsdsession)
                        qoreq["order_id"] = orec["order_id"]
                        qoreq.send()
                        qoresp = jsd.QueryOrderResp(self.jsdsession)
                        qoresp.recv()
                        self.logger.info("query response when cancel open failed: %s", str(qoresp.records))
                        if qoresp.anwser == "Y":
                            #partial done, partial deleted
                            if qoresp.records[0][1] == "b":
                                self.sindexinfo["state"] = Portfolio.IFCANCELOPENSHORTOK
                            elif qoresp.records[0][1] == "c":
                                self.sindexinfo["state"] = Portfolio.IFOPENSHORTOK
                            else:
                                self.logger.error("unhandled order state when cancel")
                        else:
                            self.logger.error("error when query cancel-failed order")
            else:
                self.logger.info("not in cancelopen-able state")

    def closeshort(self):
        with self.sindexlock:
            if self.sindexinfo["state"] in (Portfolio.IFOPENSHORTOK,
                    Portfolio.IFCANCELOPENSHORTOK, Portfolio.IFCANCELCLOSESHORTOK):

                candoclose = True
                closecount = 0
                if self.sindexinfo["state"] == Portfolio.IFOPENSHORTOK:
                    # check opened count equals expected count
                    if int(self.sindexinfo["count"]) != self.sindexinfo["opencount"]:
                        candoclose = False
                        self.logger.warning("stock index opened and still waiting for deal, cannot close")
                    else:
                        # close count = opened count = expected count
                        closecount = int(self.sindexinfo["count"])
                elif self.sindexinfo["state"] == Portfolio.IFCANCELOPENSHORTOK:
                    # close count = opened count
                    closecount = self.sindexinfo["opencount"]
                    #assert self.sindexinfo["opencount"] < int(self.sindexinfo["count"])
                elif self.sindexinfo["state"] == Portfolio.IFCANCELCLOSESHORTOK:
                    # close count = opened count - closed count
                    closecount = self.sindexinfo["opencount"] - self.sindexinfo["closecount"]
                    # assert close count > 0 here

                if closecount <= 0:
                    candoclose = False

                if candoclose:
                    oreq = jsd.OrderReq(self.jsdsession)
                    oreq["exchcode"] = self.jsdsession["cffexcode"]
                    oreq["code"] = self.sindexinfo["code"]
                    oreq["longshort"] = "0"
                    oreq["openclose"] = "1"
                    oreq["ifhedge"] = "0"
                    assert closecount > 0
                    oreq["count"] = str(closecount)
                    oreq["price"] = "%0.1f" % self.sindexinfo["closeposprice"]
                    oreq["clientnum"] = self.jsdsession["clientnum"]
                    oreq["seat"] = self.jsdsession["seat"]
                    oreq.send()
                    sirec = SIndexRecord()
                    self.sindexinfo["pastclose"].append(sirec)
                    oresp = jsd.OrderResp(self.jsdsession)
                    oresp.recv()
                    resp = oresp.records[0]
                    print resp
                    if oresp.anwser == "Y":
                        # NOTE: order state may change after ordering
                        sirec["order_id"] = resp[1]
                        sirec["order_date"] = str(datetime.today().date())
                        sirec["order_time"] = str(datetime.now().time())
                        sirec["ordercount"] = resp[14]
                        sirec["orderprice"] = resp[15]
                        sirec["longshort"] = oreq["longshort"]
                        sirec["openclose"] = oreq["openclose"]
                        sirec["ifhedge"] = oreq["ifhedge"]
                        sirec["orderseat"] = resp[30]
                        sirec["syscenter"] = resp[19]
                        self.sindexinfo["state"] = Portfolio.IFCLOSESHORTOK
                        # TODO: test storetrade ok
                    elif oresp.anwser == "N":
                        resp = oresp.records[0]
                        sirec["order_date"] = str(datetime.today().date())
                        sirec["order_time"] = str(datetime.now().time())
                        sirec["ordercount"] = oreq["count"]
                        sirec["orderprice"] = oreq["price"]
                        sirec["longshort"] = oreq["longshort"]
                        sirec["openclose"] = oreq["openclose"]
                        sirec["ifhedge"] = oreq["ifhedge"]
                        self.sindexinfo["state"] = Portfolio.IFCLOSESHORTFAILED
                        # TODO: test storetrade ok
                    else:
                        self.logger.warning("unknow order response: %s" % str(oresp.records))

            else:
                self.logger.info("not in close-able state")

    def cancelcloseshort(self):
        with self.sindexlock:
            if self.sindexinfo["state"] == Portfolio.IFCLOSESHORTOK:
                if self.sindexinfo["closecount"] < self.sindexinfo["opencount"]:
                    si = self.sindexinfo
                    orec = None
                    if len(si["pastclose"]) != 0:
                        orec = si["pastclose"][-1]
                    #elif len(si["pastopen"]) != 0:
                    #    orec = si["pastopen"][-1]
                    if orec == None:
                        self.logger.warning("cancel without a previous close.")
                        return

                    coreq = jsd.CancelOrderReq(self.jsdsession)
                    coreq["exchcode"] = self.jsdsession["cffexcode"]
                    coreq["code"] = si["code"]
                    coreq["longshort"] = orec["longshort"]
                    coreq["openclose"] = orec["openclose"]
                    coreq["ifhedge"] = orec["ifhedge"]
                    coreq["count"] = orec["ordercount"]
                    coreq["price"] = orec["orderprice"]
                    coreq["order_id"] = orec["order_id"]
                    coreq["cancelcount"] = str( si["opencount"] - si["closecount"] )
                    coreq["syscenter"] = orec["syscenter"]
                    coreq["seat"] = self.jsdsession["seat"]
                    coreq["orderseat"] = orec["orderseat"]
                    coreq.send()
                    coresp = jsd.CancelOrderResp(self.jsdsession)
                    coresp.recv()
                    self.logger.info("cancel close response: %s", str(coresp.records))
                    if coresp.anwser == "Y":
                        self.sindexinfo["state"] = Portfolio.IFCANCELCLOSESHORTOK
                    else:
                        # check order state, if order already canceled, or totally
                        # dealed, its state should be ok
                        self.sindexinfo["state"] = Portfolio.IFCANCELCLOSESHORTFAILED
                        qoreq = jsd.QueryOrderReq(self.jsdsession)
                        qoreq["order_id"] = orec["order_id"]
                        qoreq.send()
                        qoresp = jsd.QueryOrderResp(self.jsdsession)
                        qoresp.recv()
                        self.logger.info("query response when cancel close failed: %s", str(qoresp.records))
                        if qoresp.anwser == "Y":
                            #partial done, partial deleted
                            if qoresp.records[0][1] == "b":
                                self.sindexinfo["state"] = Portfolio.IFCANCELCLOSESHORTOK
                            elif qoresp.records[0][1] == "c":
                                self.sindexinfo["state"] = Portfolio.IFCLOSESHORTOK
                            else:
                                self.logger.error("unhandled order state when cancel")
                        else:
                            self.logger.error("error when query cancel-failed order")

            else:
                self.logger.info("not in cancelclose-able state")

    def makesiforder(self, code, price, share, openclose, longshort):
        oreq = jsd.OrderReq(self.jsdsession)
        oresp = jsd.OrderResp(self.jsdsession)
        oreq.makeorder(code, price, share, openclose, longshort)
        oreq.send()
        oresp.recv()
        sirec = SIndexRecord()
        sirec.updatefrom(oreq, oresp)
        return sirec

    def cancelsiforder(self, sirec, cancelcount):
        coreq = jsd.CancelOrderReq(self.jsdsession)
        coresp = jsd.CancelOrderResp(self.jsdsession)
        coreq.makecancelorder(sirec, cancelcount)
        coreq.send()
        coresp.recv()
        return coresp

    # TODO: remove FOUR duplicated functions below.
    def openshort2(self, code, price, share):
        oreq = jsd.OrderReq(self.jsdsession)
        oresp = jsd.OrderResp(self.jsdsession)
        oreq.makeopenshort(code, price, share)
        oreq.send()
        oresp.recv()
        sirec = SIndexRecord()
        sirec.updatefrom(oresp)
        return sirec

    def closeshort2(self, code, price, share):
        oreq = jsd.OrderReq(self.jsdsession)
        oresp = jsd.OrderResp(self.jsdsession)
        oreq.makecloseshort(code, price, share)
        oreq.send()
        oresp.recv()
        sirec = SIndexRecord()
        sirec.updatefrom(oresp)
        return sirec

    def openlong2(self, code, price, share):
        oreq = jsd.OrderReq(self.jsdsession)
        oresp = jsd.OrderResp(self.jsdsession)
        oreq.makeopenlong(code, price, share)
        oreq.send()
        oresp.recv()
        sirec = SIndexRecord()
        sirec.updatefrom(oresp)
        return sirec

    def closelong2(self, code, price, share):
        oreq = jsd.OrderReq(self.jsdsession)
        oresp = jsd.OrderResp(self.jsdsession)
        oreq.makecloselong(code, price, share)
        oreq.send()
        oresp.recv()
        sirec = SIndexRecord()
        sirec.updatefrom(oresp)
        return sirec

    def updateopencount(self):
        # used in SIFOrderPushee, with sindexlock already acquired
        oc = 0
        for o in self.sindexinfo["pastopen"]:
            oid = o["order_id"]
            if oid != "" and oid in self.sindexinfo["deals"]:
                for d in self.sindexinfo["deals"][oid]:
                    oc = oc + d[0]
        self.sindexinfo["opencount"] = oc

    def updateclosecount(self):
        # used in SIFOrderPushee, with sindexlock already acquired
        cc = 0
        for o in self.sindexinfo["pastclose"]:
            oid = o["order_id"]
            if oid != "" and oid in self.sindexinfo["deals"]:
                for d in self.sindexinfo["deals"][oid]:
                    cc = cc + d[0]
        self.sindexinfo["closecount"] = cc

    def updateearning(self):
        gain = 0.0
        paid = 0.0

        for o in self.sindexinfo["pastopen"]:
            oid = o["order_id"]
            if oid != "" and oid in self.sindexinfo["deals"]:
                for d in self.sindexinfo["deals"][oid]:
                    gain = gain + d[0] * d[1]
        for o in self.sindexinfo["pastclose"]:
            oid = o["order_id"]
            if oid != "" and oid in self.sindexinfo["deals"]:
                for d in self.sindexinfo["deals"][oid]:
                    paid = paid + d[0] * d[1]
        self.sindexinfo["earning"] = 0.0
        self.sindexinfo["openavg"] = 0.0
        self.sindexinfo["closeavg"] = 0.0
        try:
            self.sindexinfo["earning"] = gain - paid - self.sindexinfo["latestprice"] * (self.sindexinfo["opencount"] - self.sindexinfo["closecount"])
            self.sindexinfo["openavg"] = gain / self.sindexinfo["opencount"]
            self.sindexinfo["closeavg"] = paid / self.sindexinfo["closecount"]
        except KeyError:#latestprice is not updated
            pass
        except ZeroDivisionError:
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

class PortfolioUpdater_dbf(Thread):
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
        self.hookquote = {}
        self.name = self.__class__.__name__
        self.logger = logging.getLogger()

        # one-to-one mapping of dbfield to stockattr, for SH
        self.shdbfield = ["S2", "S3", "S4", "S8"]#, "S9", "S10"]
        self.shdbmapping = {
                "S2":"name",
                "S3":"close",
                "S4":"open",
                "S8":"latestprice"
                }
        assert(len(self.shdbfield) == len(self.shdbmapping))

        # for SZ
        self.szdbfield = ["HQZRSP", "HQJRKP", "HQZQJC", "HQZJCJ"]#, "HQBJW1", "HQSJW1"]
        self.szdbmapping = {
                "HQZQJC":"name",
                "HQZRSP":"close",
                "HQJRKP":"open",
                "HQZJCJ":"latestprice"
                }
        assert(len(self.szdbfield) == len(self.szdbmapping))

    def close(self):
        self.dbsh.close()
        self.dbsz.close()

    def addhook(self, code):
        self.hookquote[code] = None

    def gethookquote(self, code):
        try:
            return self.hookquote[code]
        except KeyError:
            return None

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

        for scode in self.hookquote:
            if scode[0:2] == "SH":
                self.hookquote[scode] = dbsh[shmap[scode]]
            if scode[0:2] == "SZ":
                self.hookquote[scode] = dbsz[szmap[scode]]

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
            #rowindex = self.portfolio.stocklist.index(scode)
            #QMetaObject.invokeMethod(self.portmodel,
            #        "updaterow", Qt.QueuedConnection,
            #        Q_ARG("int", rowindex))

        QMetaObject.invokeMethod(self.portmodel, "updateall", Qt.QueuedConnection)

    def genorderlist(self):
        mktvallist = []
        for scode in self.portfolio.stocklist:
            si = self.portfolio.stockinfo[scode]
            mktvallist.append( (scode, si["close"]*int(si["count"])) )
        mktvallist.sort(key=lambda x:x[1], reverse=True)
        orderlist = [ x[0] for x in mktvallist ]
        self.portfolio.orderlist = orderlist
        self.logger.info("stock order sequence is: \n%s" %
                str(self.portfolio.orderlist))

    def stop(self):
        self.runflag = False

    def run(self):
        try:
            self.update()
            self.genorderlist()
            while self.runflag:
                time.sleep(2)
                self.update()
            self.close()
        except Exception:
            self.logger.exception("Oh!!!")

class PortfolioUpdater_net(Thread):
    def __init__(self, servhost, servport, portfolio, portmodel):
        Thread.__init__(self)
        self.servhost = servhost
        self.servport = servport
        self.conn = None
        self.portfolio = portfolio
        self.pmodel = portmodel
        self.hookquote = {}
        self.runflag = True
        self.name = self.__class__.__name__
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

    def addhook(self, code):
        self.hookquote[code] = None

    def gethookquote(self, code):
        try:
            return self.hookquote[code]
        except KeyError:
            return None

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

        for rec in data["SH"]:
            scode = "SH"+rec["S1"]
            if scode in self.portfolio.stocklist:
                stockinfo = self.portfolio.stockinfo[scode]
                for f in self.shdbfield:
                    if type(rec[f]) is types.StringType:
                        stockinfo[self.shdbmapping[f]] = rec[f].decode("GBK")
                    else:
                        stockinfo[self.shdbmapping[f]] = rec[f]
                stockinfo["tobuyprice"] = self.getpricesh(rec, self.portfolio.buypolicy) + self.portfolio.buypricefix
                stockinfo["tosellprice"] = self.getpricesh(rec, self.portfolio.sellpolicy) + self.portfolio.sellpricefix

                rowindex = self.portfolio.stocklist.index(scode)
            elif scode in self.hookquote:
                self.hookquote[scode] = rec

        for rec in data["SZ"]:
            scode = "SZ"+rec["HQZQDM"]
            if scode in self.portfolio.stocklist:
                stockinfo = self.portfolio.stockinfo[scode]
                for f in self.szdbfield:
                    if type(rec[f]) is types.StringType:
                        stockinfo[self.szdbmapping[f]] = rec[f].decode("GBK")
                    else:
                        stockinfo[self.szdbmapping[f]] = rec[f]
                stockinfo["tobuyprice"] = self.getpricesz(rec, self.portfolio.buypolicy) + self.portfolio.buypricefix
                stockinfo["tosellprice"] = self.getpricesz(rec, self.portfolio.sellpolicy) + self.portfolio.sellpricefix

                rowindex = self.portfolio.stocklist.index(scode)
            elif scode in self.hookquote:
                self.hookquote[scode] = rec

        QMetaObject.invokeMethod(self.pmodel, "updateall", Qt.QueuedConnection)

    def stop(self):
        self.runflag = False

    def genorderlist(self):
        mktvallist = []
        for scode in self.portfolio.stocklist:
            si = self.portfolio.stockinfo[scode]
            mktvallist.append( (scode, si["close"]*int(si["count"])) )
        mktvallist.sort(key=lambda x:x[1], reverse=True)
        orderlist = [ x[0] for x in mktvallist ]
        self.portfolio.orderlist = orderlist
        self.logger.info("stock order sequence is: \n%s" %
                str(self.portfolio.orderlist))

    def run(self):
        try:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.connect((self.servhost, self.servport))
        except socket.error:
            self.logger.exception("cannot connect to quoteserver")
            return

        try:
            self.update()
            self.genorderlist()
            while self.runflag:
                self.update()
        except Exception:
            self.logger.exception("Oh!!!")
        finally:
            self.conn.close()

class SecuInfoUpdater(Thread):
    def __init__(self, portfolio, pmodel, sessioncfg):
        """
        Update floor/ceiling price and stop flag,
        I think updater lock is not needed here
        """
        Thread.__init__(self)
        self.portfolio = portfolio
        self.pmodel = pmodel
        self.sessioncfg = sessioncfg
        self.session = None
        self.runflag = True
        self.evt = Event()
        self.logger = logging.getLogger()
        self.name = self.__class__.__name__

    def update(self):
        rowindex = -1
        for scode in self.portfolio.stocklist:
            rowindex += 1
            si = self.portfolio.stockinfo[scode]
            sireq = jz.SecuInfoReq(self.session)
            mkt = si["market"]
            code = si["code"]
            if mkt == "SH":
                sireq["market"] = jz.SHAMARKET
            elif mkt == "SZ":
                sireq["market"] = jz.SZAMARKET
            sireq["secu_code"] = code
            sireq.send()
            siresp = jz.SecuInfoResp(self.session)
            siresp.recv()
            if siresp.retcode == "0":
                si["ceiling"] = float(siresp.records[0][10])
                si["floor"] = float(siresp.records[0][11])
                si["stopped"] = (siresp.records[0][12] == "1")
                QMetaObject.invokeMethod(self.pmodel, "updaterow", Qt.QueuedConnection,
                        Q_ARG("int", rowindex))

    def stop(self):
        self.runflag = False
        self.evt.set()

    def close(self):
        if self.session:
            self.session.close()
            self.session = None

    def run(self):
        try:
            self.session = jz.session(self.sessioncfg)
            if not self.session.setup():
                self.logger.warning("Session setup failed.")
                self.close()
                return

            while self.runflag:
                self.update()
                self.evt.wait(300)#5mins

            self.close()
        except Exception:
            self.logger.exception("Oh!!!")

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
        self.name = self.__class__.__name__

    def close(self):
        if self.jsdsession:
            self.jsdsession.close()
            self.jsdsession = None

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
        try:
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
        except Exception:
            self.logger.exception("Oh!!!")

class SIFPriceUpdater_pushee(Thread):
    def __init__(self, portfolio, sindexmodel, jsdcfg, uic):
        """
        note: only one pushee on a machine can receive price, other pushee will receive none
        """
        Thread.__init__(self)
        self.portfolio = portfolio
        self.sindexmodel = sindexmodel
        self.jsdcfg = jsdcfg
        self.jsdsession = None
        self.uic = uic
        self.runflag = True
        self.columnresized = False
        self.logger = logging.getLogger()
        self.name = self.__class__.__name__

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
                if self.portfolio.openpolicy == "mktval":
                    si["openposprice"] = 0.0
                else:
                    si["openposprice"] = self.getsindexprice(qd, self.portfolio.openpolicy) + self.portfolio.openpricefix
                if self.portfolio.closepolicy == "mktval":
                    si["closeposprice"] = 0.0
                else:
                    si["closeposprice"] = self.getsindexprice(qd, self.portfolio.closepolicy) + self.portfolio.closepricefix
                self.portfolio.updateearning()

                if not self.columnresized:
                    self.uic.stockindex.resizeColumnsToContents()
                    self.columnresized = True
                QMetaObject.invokeMethod(self.sindexmodel, "updaterow", Qt.QueuedConnection)

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
        try:
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
            MAX_QUOTA_ITEM_COUNT = 50
            quotaData = (jsdhq.KSFT_QUOTA_PUBDATA_ITEM * MAX_QUOTA_ITEM_COUNT)()
            while self.runflag:
                qcount = KSFTHQPUB_GetQuota(cast(quotaData, c_char_p),
                        sizeof(jsdhq.KSFT_QUOTA_PUBDATA_ITEM)*MAX_QUOTA_ITEM_COUNT,
                        timeout,
                        errmsg)
                if qcount < 0:
                    self.logging.warning("Error while receiving hq: %s", errmsg)
                elif qcount > 0:
                    self.updateprice(quotaData, qcount)
                else:
                    pass

            KSFTHQPUB_Stop()
        except Exception:
            self.logger.exception("Oh!!!")

class SIFPriceUpdater_net(Thread):
    def __init__(self, servhost, servport, portfolio, sindexmodel, uic):
        Thread.__init__(self)
        self.servhost = servhost
        self.servport = servport
        self.portfolio = portfolio
        self.sindexmodel = sindexmodel
        self.uic = uic
        self.conn = None
        self.runflag = True
        self.columnresized = False
        self.logger = logging.getLogger()
        self.name = self.__class__.__name__

    def getsindexprice(self, qd, pricepolicy):
        policymapping = {
                "latest":"lastPrice",
                "b1":"bidPrice1",
                "s1":"askPrice1"
                }
        return getattr(qd, policymapping[pricepolicy])

    def stop(self):
        self.runflag = False

    def updateprice(self, quotaData):
        for qd in quotaData:
            si = self.portfolio.sindexinfo
            if qd.varity_code+qd.deliv_date == si["code"]:
                si["latestprice"] = qd.lastPrice
                si["open"] = qd.openPrice
                si["close"] = qd.preClosePrice
                si["ceiling"] = qd.upperLimitPrice
                si["floor"] = qd.lowerLimitPrice
                if self.portfolio.openpolicy == "mktval":
                    si["openposprice"] = 0.0
                else:
                    si["openposprice"] = self.getsindexprice(qd, self.portfolio.openpolicy) + self.portfolio.openpricefix
                if self.portfolio.closepolicy == "mktval":
                    si["closeposprice"] = 0.0
                else:
                    si["closeposprice"] = self.getsindexprice(qd, self.portfolio.closepolicy) + self.portfolio.closepricefix
                self.portfolio.updateearning()

                if not self.columnresized:
                    self.uic.stockindex.resizeColumnsToContents()
                    self.columnresized = True
                QMetaObject.invokeMethod(self.sindexmodel, "updaterow", Qt.QueuedConnection)

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

    def run(self):
        try:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.connect((self.servhost, self.servport))
        except socket.error:
            self.logger.exception("cannot connect to quoteserver")
            return

        try:
            while self.runflag:
                self.update()
        except Exception:
            self.logger.exception("Oh!!!")
        finally:
            self.conn.close()

class SIFOrderUpdater(Thread):
    def __init__(self, portfolio, sindexmodel, jsdcfg):
        Thread.__init__(self)
        self.portfolio = portfolio
        self.sindexmodel = sindexmodel
        self.jsdcfg = jsdcfg
        self.sindexlock = portfolio.sindexlock
        self.name = self.__class__.__name__
        self.logger = logging.getLogger()
        self.session = None
        self.runflag = True

    def close(self):
        if self.session:
            self.session.close()
            self.session = None

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
        try:
            s = jsd.session(self.jsdcfg)
            if not s.setup():
                self.logger.warning("Cannot login")
                return False
            self.session = s

            while self.runflag:
                self.update()
                time.sleep(1)

            self.close()
        except Exception:
            self.logger.exception("Oh!!!")

class SIFOrderUpdaterQ(Thread):
    """
    order updater for orders from quick operation
    """
    def __init__(self, portfolio, jsdcfg, uic):
        Thread.__init__(self)
        self.portfolio = portfolio
        self.jsdcfg = jsdcfg
        self.uic = uic
        self.name = self.__class__.__name__
        self.logger = logging.getLogger()
        self.session = None
        self.runflag = True

    def close(self):
        if self.session:
            self.session.close()
            self.session = None

    def update(self):
        sirec = self.portfolio.sifquickinfo
        if sirec["order_id"] and sirec["ordercount"] != sirec["dealcount"]:
            qreq = jsd.QueryOrderReq(self.session)
            qreq["order_id"] = sirec["order_id"]
            qreq.send()
            qresp = jsd.QueryOrderResp(self.session)
            qresp.recv()
            if qresp.anwser == "Y":
                dealcnt = qresp.records[0][2]
                if dealcnt != sirec["dealcount"]:
                    sirec["dealcount"] = dealcnt
                    QMetaObject.invokeMethod(self.uic.sifdcntline, "setText",
                            Qt.QueuedConnection,
                            Q_ARG("QString",
                                QString(dealcnt)))
            else:
                print "query error", qresp.failinfo

    def stop(self):
        self.runflag = False

    def run(self):
        try:
            s = jsd.session(self.jsdcfg)
            if not s.setup():
                self.logger.warning("Cannot login")
                return False
            self.session = s

            while self.runflag:
                self.update()
                time.sleep(1)

            self.close()
        except Exception:
            self.logger.exception("Oh!!!")

class SIFOrderPushee(Thread):
    """
    note:
    
    1. if an order is dealed immediatelly, the result will be sent in order response, and not
    further deal response will be received.
    2. sometimes, no order response, only deal response
    3. check order_id, pushee will receive all messages, including orders submitted in other programs
    """
    def __init__(self, portfolio, sindexmodel, jsdcfg):
        Thread.__init__(self)
        self.portfolio = portfolio
        self.sindexmodel = sindexmodel
        self.jsdcfg = jsdcfg
        self.sindexlock = portfolio.sindexlock
        self.name = self.__class__.__name__
        self.logger = logging.getLogger()
        self.session = None
        self.runflag = True
        self.conn = None
        self.msghandler = {
                8001:self.nonehdl,# connected
                8002:self.orderhdl,
                8003:self.cancelhdl,
                8008:self.dealhdl,
                8009:self.statechagehdl,
                8010:self.infohdl,
                8020:self.ponghdl# pong
                }

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def parsedata(self, data):
        data = data.strip("|")
        rec = data.split("|")
        return rec

    def getOrderRec(self):
        si = self.portfolio.sindexinfo
        ret = None
        try:
            if len(si["pastclose"]) != 0:
                ret = si["pastclose"][-1]
            elif len(si["pastopen"]) != 0:
                ret = si["pastopen"][-1]
        except KeyError:#happens when no IF code is included in ptf
            pass
        return ret

    def nonehdl(self, cmd, length, data):
        self.logger.info("SIFOrderPushee receive message: %d, %d, %s", cmd, length, data)

    def ponghdl(self, cmd, length, data):
        # silent when ponged
        pass

    def orderhdl(self, cmd, length, data):
        # only update deal count?
        # NOTE: assumption: even it's dealed in OrderResp, we can also get a copy of
        # deal info here, so we ignore deal info in OrderResp, and update deal info here and
        # in dealhdl
        self.logger.info("SIFOrderPushee receive order response: %d, %d, %s", cmd, length, data)
        rec = self.parsedata(data)
        sirec = self.getOrderRec()
        if sirec is None or rec[6] != sirec["order_id"]:
            self.logger.info("Receive an order that's not issued by me.")
            return

        si = self.portfolio.sindexinfo
        if rec[11] in "pc":#partial or total complete
            oid = rec[6]
            si["deals"].setdefault(oid, [])
            # count, price
            si["deals"][oid].append(( int(rec[7]), float(rec[8]) ))
            if rec[13] == "0":#open
                self.portfolio.updateopencount()
                self.portfolio.updateearning()
            if rec[13] == "1":#close
                self.portfolio.updateclosecount()
                self.portfolio.updateearning()
        elif rec[11] in "qd":#sys/user diabled, so failed
            if rec[13] == "0":#open
                si["state"] = self.portfolio.IFOPENSHORTFAILED
            if rec[13] == "1":#close
                si["state"] = self.portfolio.IFCLOSESHORTFAILED
        else:
            self.logger.warning("unhandled order state (%s): %d, %d, %s",
                    rec[11], cmd, length, data)

    def cancelhdl(self, cmd, length, data):
        self.logger.info("SIFOrderPushee receive cancel response: %d, %d, %s", cmd, length, data)
        pass

    def dealhdl(self, cmd, length, data):
        self.logger.info("SIFOrderPushee receive deal response: %d, %d, %s", cmd, length, data)
        rec = self.parsedata(data)
        sirec = self.getOrderRec()
        if sirec is None or rec[7] != sirec["order_id"]:
            self.logger.info("Receive an order that's not issued by me.")
            return

        si = self.portfolio.sindexinfo
        if rec[14] in "pcf":#partial or total complete or deleting
            oid = rec[7]
            si["deals"].setdefault(oid, [])
            si["deals"][oid].append(( int(rec[8]), float(rec[9]) ))
            if rec[16] == "0":#open
                self.portfolio.updateopencount()
                self.portfolio.updateearning()
            if rec[16] == "1":#close
                self.portfolio.updateclosecount()
                self.portfolio.updateearning()
        else:
            self.logger.warning("unhandled state: %d, %d, %s",
                    cmd, length, data)

    def statechagehdl(self, cmd, length, data):
        self.logger.info("SIFOrderPushee receive state change msg: %d, %d, %s", cmd, length, data)

    def infohdl(self, cmd, length, data):
        self.logger.info("SIFOrderPushee receive some infomation: %d, %d, %s", cmd, length, data)

    def setup(self):
        ret = True
        self.conn = socket.socket()
        try:
            self.conn.connect((self.jsdcfg["jsdserver"],
                self.jsdcfg["jsdport"]+2))
            self.conn.settimeout(6)
        except socket.error:
            self.logger.warning("cannot connect to push address")
            ret = False
        return ret

    def update(self):
        try:
            data = self.conn.recv(4)
            (cmd, length) = unpack("!HH", data)
            data = ""
            if length > 0:
                data = self.conn.recv(length)
                data = data.decode("GBK")
            hdl = self.msghandler[cmd]
            with self.sindexlock:
                # TODO: race condition may exist between operations caused by buttons, e.g. open/close/cancel
                hdl(cmd, length, data)
            QMetaObject.invokeMethod(self.sindexmodel, "updaterow", Qt.QueuedConnection)
        except socket.timeout:
            # ping
            self.conn.send(pack("!HH", 20, 0))

    def stop(self):
        self.runflag = False

    def run(self):
        try:
            if not self.setup():
                self.logger.warning("SIFOrderPushee cannot setup itself")
                return

            # send connect signal
            self.conn.send(pack("!hh", 1, 0))
            while self.runflag:
                self.update()
            self.close()
        except Exception:
            self.logger.exception("Oh!!!")

class StockStatUpdater(Thread):
    def __init__(self, ui, portfolio, pstat):
        Thread.__init__(self)
        self.ui = ui
        self.portfolio = portfolio
        self.pstat = pstat
        self.runflag = True
        self.name = self.__class__.__name__
        self.logger = logging.getLogger()

    def stop(self):
        self.runflag = False

    def run(self):
        while self.runflag:
            try:
                buytotal = 0.0
                selltotal = 0.0

                stopped = 0
                buyable = 0
                buycomplete = 0
                buywait = 0
                buyfail = 0
                cancelbuyfail = 0

                sellable = 0
                sellcomplete = 0
                sellwait = 0
                sellfail = 0
                cancelsellfail = 0

                for scode in self.portfolio.orderlist:
                    si = self.portfolio.stockinfo[scode]
                    buytotal = buytotal + si["currentbuycost"]
                    selltotal = selltotal + si["pastsellgain"]

                    try:
                        if si["stopped"]:
                            stopped = stopped + 1
                        if self.portfolio.isvalidbuy(si, scode):
                            buyable = buyable + 1
                        if si["pastbuy"]:
                            ob = si["pastbuy"][-1]
                            if ob["dealcount"] == ob["ordercount"]:
                                buycomplete = buycomplete + 1
                            if ob["order_state"] == Portfolio.CANCELBUYWAIT:
                                buywait = buywait + 1
                            elif ob["order_state"] == Portfolio.BUYFAILED:
                                buyfail = buyfail + 1
                            elif ob["order_state"] == Portfolio.CANCELBUYFAILED:
                                cancelbuyfail = cancelbuyfail + 1

                        if self.portfolio.isvalidsell(si, scode):
                            sellable = sellable + 1
                        if si["pastsell"]:
                            ob = si["pastsell"][-1]
                            if ob["dealcount"] == ob["ordercount"]:
                                sellcomplete = sellcomplete + 1
                            if ob["order_state"] == Portfolio.CANCELSELLWAIT:
                                sellwait = sellwait + 1
                            elif ob["order_state"] == Portfolio.SELLFAILED:
                                sellfail = sellfail + 1
                            elif ob["order_state"] == Portfolio.CANCELSELLFAILED:
                                cancelsellfail = cancelsellfail + 1
                    except KeyError:
                        pass

                QMetaObject.invokeMethod(self.ui.stoppedline, "setText",
                        Qt.QueuedConnection,
                        Q_ARG("QString",
                            QString(u"%d"%stopped)))
                QMetaObject.invokeMethod(self.ui.stoppedline_2, "setText",
                        Qt.QueuedConnection,
                        Q_ARG("QString",
                            QString(u"%d"%stopped)))

                # buy stats
                QMetaObject.invokeMethod(self.ui.buyableline, "setText",
                        Qt.QueuedConnection,
                        Q_ARG("QString",
                            QString(u"%d"%buyable)))

                QMetaObject.invokeMethod(self.ui.buyedline, "setText",
                        Qt.QueuedConnection,
                        Q_ARG("QString",
                            QString(u"%d"%buycomplete)))

                QMetaObject.invokeMethod(self.ui.buywaitline, "setText",
                        Qt.QueuedConnection,
                        Q_ARG("QString",
                            QString(u"%d"%buywait)))

                QMetaObject.invokeMethod(self.ui.buyfailline, "setText",
                        Qt.QueuedConnection,
                        Q_ARG("QString",
                            QString(u"%d"%buyfail)))

                QMetaObject.invokeMethod(self.ui.cancelbuyfailline, "setText",
                        Qt.QueuedConnection,
                        Q_ARG("QString",
                            QString(u"%d"%cancelbuyfail)))

                # sell stats
                QMetaObject.invokeMethod(self.ui.sellableline, "setText",
                        Qt.QueuedConnection,
                        Q_ARG("QString",
                            QString(u"%d"%sellable)))

                QMetaObject.invokeMethod(self.ui.selledline, "setText",
                        Qt.QueuedConnection,
                        Q_ARG("QString",
                            QString(u"%d"%sellcomplete)))

                QMetaObject.invokeMethod(self.ui.sellwaitline, "setText",
                        Qt.QueuedConnection,
                        Q_ARG("QString",
                            QString(u"%d"%sellwait)))

                QMetaObject.invokeMethod(self.ui.sellfailline, "setText",
                        Qt.QueuedConnection,
                        Q_ARG("QString",
                            QString(u"%d"%sellfail)))

                QMetaObject.invokeMethod(self.ui.cancelsellfailline, "setText",
                        Qt.QueuedConnection,
                        Q_ARG("QString",
                            QString(u"%d"%cancelsellfail)))

                buytotalw = buytotal / 10000
                selltotalw = selltotal / 10000

                buypoint = 0.0
                sellpoint = 0.0
                unbuymktval = 0.0
                unsellmktval = 0.0

                for scode in self.portfolio.orderlist:
                    si = self.portfolio.stockinfo[scode]
                    try:
                        closemktval = float(si["count"])*si["close"]

                        if si["currentbuycost"] == 0.0:
                            unbuymktval = unbuymktval + closemktval

                        if si["currentsellgain"] == 0.0:
                            if si["currentbuycost"] == 0.0:
                                unsellmktval = unsellmktval + closemktval
                            else:
                                unsellmktval = unsellmktval + si["currentbuycost"]
                    except KeyError:
                        pass

                try:
                    count = int(self.portfolio.sindexinfo["count"])
                    stockcount = len(self.portfolio.stocklist)
                    buypoint = (buytotal + unbuymktval) / count / stockcount
                    sellpoint = (selltotal + unsellmktval) / count / stockcount
                except Exception:
                    pass

                QMetaObject.invokeMethod(self.ui.buytotalline, "setText",
                        Qt.QueuedConnection,
                        Q_ARG("QString",
                            QString(u"%0.2f 万"%buytotalw)))

                QMetaObject.invokeMethod(self.ui.selltotalline, "setText",
                        Qt.QueuedConnection,
                        Q_ARG("QString",
                            QString(u"%0.2f 万"%selltotalw)))

                QMetaObject.invokeMethod(self.ui.buypointline, "setText",
                        Qt.QueuedConnection,
                        Q_ARG("QString",
                            QString(u"%0.2f"%buypoint)))

                QMetaObject.invokeMethod(self.ui.sellpointline, "setText",
                        Qt.QueuedConnection,
                        Q_ARG("QString",
                            QString(u"%0.2f"%sellpoint)))

                self.pstat["buytotalw"] = buytotalw
                self.pstat["selltotalw"] = selltotalw

                self.pstat["stopped"] = stopped
                self.pstat["buyable"] = buyable
                self.pstat["buycomplete"] = buycomplete
                self.pstat["buywait"] = buywait
                self.pstat["buyfail"] = buyfail
                self.pstat["cancelbuyfail"] = cancelbuyfail

                self.pstat["sellable"] = sellable
                self.pstat["sellcomplete"] = sellcomplete
                self.pstat["sellwait"] = sellwait
                self.pstat["sellfail"] = sellfail
                self.pstat["cancelsellfail"] = cancelsellfail

                self.pstat["buypoint"] = buypoint
                self.pstat["sellpoint"] = sellpoint

                self.pstat["state"] = self.portfolio.bostate
                self.pstat["shares"] = "0"
                try:
                    self.pstat["shares"] = self.portfolio.sindexinfo["count"]
                    self.pstat["openshares"] = self.portfolio.sindexinfo["opencount"]
                    self.pstat["closeshares"] = self.portfolio.sindexinfo["closecount"]
                except KeyError:
                    pass

                time.sleep(2)
            except Exception:
                    self.logger.exception("stats-er exit anormally.")
                    self.runflag = False

class OrderUpdater(Thread):
    def __init__(self, portfolio, portmodel, sessioncfg, updtlock):
        Thread.__init__(self)
        self.portfolio = portfolio
        self.portmodel = portmodel
        self.sessioncfg = sessioncfg
        self.runflag = True
        self.session = None
        self.updtlock = updtlock
        self.name = self.__class__.__name__
        self.logger = logging.getLogger()

    def close(self):
        if self.session:
            self.session.close()
            self.session = None

    def update(self):
        for scode in self.portfolio.stocklist:
            # TODO: why need this updtlock?
            with self.updtlock:
                si = self.portfolio.stockinfo[scode]
                # don't update buy if selled
                if len(si["pastsell"]) != 0:
                    order = si["pastsell"][-1]
                elif len(si["pastbuy"]) != 0:
                    order = si["pastbuy"][-1]
                else:
                    continue

                if order["order_id"] != "" and order["order_state"] in (Portfolio.BUYSUCCESS, Portfolio.SELLSUCCESS) and int(order["dealcount"]) != int(order["ordercount"]):
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
                        wdqty, dealcount, dealamount, dealprice = qoresp.getTotal()
                        if dealcount != None:
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

    def doping(self):
        mktinforeq = jz.MarketinfoReq(self.session)
        mktinforeq.send()
        mktinforesp = jz.MarketinfoResp(self.session)
        mktinforesp.recv()

    def run(self):
        try:
            self.session = jz.session(self.sessioncfg)
            if not self.session.setup():
                self.logger.warning("Session setup failed.")
                self.close()
                return

            idlecount = 0
            waitint = 2
            maxwait = 200
            while self.runflag:
                self.update()
                time.sleep(waitint)
                idlecount = idlecount + 1
                if idlecount*waitint > maxwait:
                    idlecount = 0
                    # do ping
                    self.doping()

            self.close()
        except Exception:
            self.logger.exception("Oh!!!")

class CancelOrderUpdater(Thread):
    def __init__(self, portfolio, portmodel, sessioncfg):
        Thread.__init__(self)
        self.portfolio = portfolio
        self.portmodel = portmodel
        self.sessioncfg = sessioncfg
        self.runflag = True
        self.session = None
        self.name = self.__class__.__name__
        self.logger = logging.getLogger()

    def close(self):
        if self.session:
            self.session.close()
            self.session = None

    def update(self):
        hasleft = False
        today = str(datetime.today().date())

        for scode in self.portfolio.stocklist:
            si = self.portfolio.stockinfo[scode]
            # don't update buy if selled
            if len(si["pastsell"]) != 0:
                order = si["pastsell"][-1]
            elif len(si["pastbuy"]) != 0:
                order = si["pastbuy"][-1]
            else:
                continue

            if order["order_id"] != "" and order["order_state"] in (Portfolio.CANCELBUYWAIT, Portfolio.CANCELSELLWAIT):
                # reset status for old orders directly at local.
                if order["order_date"] != today:
                    if len(si["pastsell"]) != 0:
                        if order["dealcount"] == order["ordercount"]:
                            order["order_state"] = Portfolio.SELLSUCCESS
                        else:
                            order["order_state"] = Portfolio.CANCELSELLSUCCESS
                    elif len(si["pastbuy"]) != 0:
                        if order["dealcount"] == order["ordercount"]:
                            order["order_state"] = Portfolio.BUYSUCCESS
                        else:
                            order["order_state"] = Portfolio.CANCELBUYSUCCESS

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
                ordercount = int(order["ordercount"])
                if qoresp.retcode == "0":
                    wdqty, dealcount, dealamount, dealprice = qoresp.getTotal()
                    if dealcount != None and (wdqty+dealcount==ordercount):
                        order["dealcount"] = str(dealcount)
                        order["dealamount"] = str(dealamount)
                        order["dealprice"] = str(dealprice)
                        if len(si["pastsell"]) != 0:
                            si["pastsellcount"] = si["pastsellcount"] + int(order["dealcount"])
                            si["pastsellgain"] = si["pastsellgain"] + float(order["dealamount"])
                            si["currentsellcount"] = si["pastsellcount"]
                            si["currentsellgain"] = si["pastsellgain"]
                            if order["dealcount"] == order["ordercount"]:
                                order["order_state"] = Portfolio.SELLSUCCESS
                            else:
                                order["order_state"] = Portfolio.CANCELSELLSUCCESS
                        elif len(si["pastbuy"]) != 0:
                            si["pastbuycount"] = si["pastbuycount"] + int(order["dealcount"])
                            si["pastbuycost"] = si["pastbuycost"] + float(order["dealamount"])
                            si["currentbuycount"] = si["pastbuycount"]
                            si["currentbuycost"] = si["pastbuycost"]
                            if order["dealcount"] == order["ordercount"]:
                                order["order_state"] = Portfolio.BUYSUCCESS
                            else:
                                order["order_state"] = Portfolio.CANCELBUYSUCCESS
                    else:
                        hasleft = True
                else:
                    self.logger.warning("error when query order for %s: %s, %s"
                            % (order["order_id"], qoresp.retcode, qoresp.retinfo))

                # update a row
                rowindex = self.portfolio.stocklist.index(scode)
                QMetaObject.invokeMethod(self.portmodel, "updaterow", Qt.QueuedConnection,
                        Q_ARG("int", rowindex))
        return hasleft

    def stop(self):
        self.runflag = False

    def doping(self):
        mktinforeq = jz.MarketinfoReq(self.session)
        mktinforeq.send()
        mktinforesp = jz.MarketinfoResp(self.session)
        mktinforesp.recv()

    def run(self):
        try:
            self.session = jz.session(self.sessioncfg)
            if not self.session.setup():
                self.logger.warning("Session setup failed.")
                self.close()
                return

            idlecount = 0
            waitint = 1
            maxwait = 200
            while self.runflag:
                hasleft = self.update()
                if not hasleft:
                    time.sleep(waitint)
                    idlecount = idlecount + 1
                    if idlecount*waitint > maxwait:
                        idlecount = 0
                        # do ping
                        self.doping()

        except Exception:
            self.logger.exception("Oh!!!")
        finally:
            self.close()

class jzHandler_ac(Thread):
    def __init__(self, session_cfg, concount, tqueue, dbqueue):
        Thread.__init__(self)
        self.session_cfg = session_cfg
        self.tqueue = tqueue
        self.dbqueue = dbqueue
        self.concount = concount
        self.logger = logging.getLogger()

    def run(self):
        scount = 0
        for i in range(self.concount):
            s = jz.session(self.session_cfg)
            if s.setup():
                scount += 1
                jzworker_ac(s, self.tqueue, self.dbqueue)
        self.logger.info("%d of %d session started." %
                (scount, self.concount))
        asyncore.loop(0.1)

class asyncWorker(Thread):
    def __init__(self, session_cfg, tqueue, dbqueue):
        Thread.__init__(self)
        self.session_cfg = session_cfg
        self.tqueue = tqueue
        self.dbqueue = dbqueue
        self.runflag = True
        self.name = self.__class__.__name__
        self.logger = logging.getLogger()
        self.session = None

    def setupsession(self):
        return False

    def closesession(self):
        if self.session:
            self.session.close()
            self.session = None

    def doping(self):
        pass

    def myrun(self):
        try:
            # TODO: what if easytrader is closed while tqueue is not empty
            if not self.setupsession():
                self.logger.warning("cannot setup session, and will exit.")
                self.closesession()
                return

            idlecount = 0
            waitint = 2
            maxwait = 200
            while self.runflag:
                try:
                    t = self.tqueue.get(True, waitint)
                    try:
                        self.dotask(t)
                    except Exception:
                        self.logger.exception("Exception while run some task, req (%s), param (%s)" % (str(type(t[0])), str(t[2])))
                    self.tqueue.task_done()
                except Queue.Empty:
                    idlecount = idlecount + 1
                    if idlecount*waitint > maxwait:
                        idlecount = 0
                        # do ping
                        self.doping()

            self.closesession()
        except Exception:
            self.logger.exception("Oh!!!")

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
            #self.session.storetrade(req, resp)
            self.dbqueue.put( (req, resp) )
        callback(req, resp, param)

    def stop(self):
        self.runflag = False

class jzWorker(asyncWorker):
    def __init__(self, session_cfg, tqueue, dbqueue):
        asyncWorker.__init__(self, session_cfg, tqueue, dbqueue)
        self.runflag = True
        self.name = self.__class__.__name__

    def setupsession(self):
        self.session = jz.session(self.session_cfg)
        if not self.session.setup():
            return False
        return True

    def doping(self):
        mktinforeq = jz.MarketinfoReq(self.session)
        mktinforeq.send()
        mktinforesp = jz.MarketinfoResp(self.session)
        mktinforesp.recv()
        #print "ping-pong"

class jsdWorker(asyncWorker):
    def __init__(self, session_cfg, tqueue, dbqueue):
        asyncWorker.__init__(self, session_cfg, tqueue, dbqueue)
        self.runflag = True
        self.name = self.__class__.__name__

    def setupsession(self):
        self.session = jsd.session(self.session_cfg)
        if not self.session.setup():
            return False
        return True

class dbserver(Thread):
    def __init__(self, dbname, dbqueue):
        Thread.__init__(self)
        self.dbname = dbname
        self.db = None
        self.dbqueue = dbqueue
        self.runflag = True
        self.name = self.__class__.__name__
        self.logger = logging.getLogger()

    def setup(self):
        self.db = db.connect(self.dbname, timeout=30)
        return True

    def close(self):
        if self.db:
            self.db.commit()
            self.db.close()
            self.db = None

    def run(self):
        try:
            if not self.setup():
                self.logger.warning("setup failed")
                self.close()
                return

            self.logger.info("dbserver setup ok.")
            while self.runflag:
                try:
                    t = self.dbqueue.get(True, 2)
                    try:
                        self.dotask(t)
                    except Exception:
                        self.logger.exception("dbserver dotask meets exception.")
                    self.dbqueue.task_done()
                except Queue.Empty:
                    pass

            self.close()

        except Exception:
            self.close()
            self.logger.exception("dbserver exit exceptionally.")

    def dotask(self, task):
        t = datetime.now()
        req = task[0]
        resp = task[1]
        self.db.execute('insert into rawtradeinfo values (?, ?, ?, ?)',
                (str(t),
                    req.payload.decode("GBK"),
                    resp.payload.decode("GBK"),
                    "%s:%s" % (resp.retcode, resp.retinfo)
                    ))
        self.db.commit()

    def stop(self):
        self.runflag = False

class uicontrol(QMainWindow, tradeui.Ui_MainWindow):
    def __init__(self, session_cfg, portfolio, pmodel, sindexmodel, opennew):
        QMainWindow.__init__(self)
        self.mainwindow = self#for backward code compatibility
        self.session_cfg = session_cfg
        self.portfolio = portfolio
        self.pmodel = pmodel
        self.sindexmodel = sindexmodel
        self.portfolio.uic = self
        self.opennew = opennew
        self.logger = logging.getLogger()

    def closeEvent(self, evt):
        ret = QMessageBox.warning(self.mainwindow,
                u"",
                u"<FONT COLOR='#FF0000'>退出交易？</FONT>",
                QMessageBox.Ok|QMessageBox.Cancel)
        if QMessageBox.Ok == ret:
            evt.accept()
        else:
            evt.ignore()

    def setup(self):
        self.setupUi(self.mainwindow)
        self.setWindowTitle(self.windowTitle() + " - " + self.portfolio.ptfn)

        icon = QIcon()
        icon.addPixmap(QBitmap(":/img/ztzq.ico"), QIcon.Normal, QIcon.On)
        self.setWindowIcon(icon)

        #icon = QIcon()
        #icon.addPixmap(QPixmap("ztzq.ico"), QIcon.Normal, QIcon.On)
        #self.mainwindow.setWindowIcon(icon)

        if self.opennew:
            self.optab.setCurrentIndex(0)
        else:
            self.optab.setCurrentIndex(1)

        # setup position name in operation
        self.posnameline.setText(os.path.basename(self.portfolio.ptfn)[0:-4])

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
        self.mainwindow.connect(self.buyorder2, SIGNAL("clicked()"), self.buyBatch2)
        self.mainwindow.connect(self.cancelbuyorder, SIGNAL("clicked()"), self.cancelBuyBatch)
        self.mainwindow.connect(self.sellorder, SIGNAL("clicked()"), self.sellBatch)
        self.mainwindow.connect(self.sellorder2, SIGNAL("clicked()"), self.sellBatch2)
        self.mainwindow.connect(self.cancelsellorder, SIGNAL("clicked()"), self.cancelSellBatch)

        # setup force buy/sell checkbox
        self.portfolio.forcecancelbuy = self.forcecancelbuychk.isChecked()
        self.portfolio.forcecancelsell = self.forcecancelsellchk.isChecked()
        self.mainwindow.connect(self.forcecancelbuychk, SIGNAL("stateChanged(int)"), self.setforcecancelbuy)
        self.mainwindow.connect(self.forcecancelsellchk, SIGNAL("stateChanged(int)"), self.setforcecancelsell)

        # setup stock index button
        self.mainwindow.connect(self.opensifbtn, SIGNAL("clicked()"), self.openshort)
        self.mainwindow.connect(self.cancelopensifbtn, SIGNAL("clicked()"), self.cancelopen)
        self.mainwindow.connect(self.closesifbtn, SIGNAL("clicked()"), self.closeshort)
        self.mainwindow.connect(self.cancelclosesifbtn, SIGNAL("clicked()"), self.cancelclose)

        # setup shortcut stock index operations
        self.mainwindow.connect(self.sifsubmitbtn, SIGNAL("clicked()"), self.sifsubmit)
        self.mainwindow.connect(self.sifcancelbtn, SIGNAL("clicked()"), self.sifcancel)

        # setup menu
        self.mainwindow.connect(self.stockinfoact, SIGNAL("triggered()"), self.showstockinfo)
        self.mainwindow.connect(self.posstatact, SIGNAL("triggered()"), self.showposstat)
        self.mainwindow.connect(self.genbuyfromsellact, SIGNAL("triggered()"), self.genbuyfromsell)
        self.mainwindow.connect(self.saveptfact, SIGNAL("triggered()"), self.savePortfolio)

        # update status lineedit
        self.showbostate()

        # setup console output from stdout
        self.logtext.write = lambda txt: self.logtext.appendPlainText(QString(txt))
        #sys.stdout = self.logtext
        #sys.stderr = self.logtext

    @pyqtSlot()
    def buyBatch(self):
        ret = QMessageBox.warning(self.mainwindow,
                u"",
                u"<H3>确认买入股票组合？（买入档位：<FONT COLOR='#FF0000'>%s</FONT>，价格修正：<FONT COLOR='#FF0000'>%s</FONT>）</H3>"
                % (self.portfolio.pricepolicynamemap[self.portfolio.buypolicy],
                    self.portfolio.buypricefix),
                QMessageBox.Ok|QMessageBox.Cancel)
        if QMessageBox.Ok == ret:
            # self.portfolio.pricepolicynamemap[self.portfolio.buypolicy], self.buypricefix
            self.portfolio.buyBatch()

    @pyqtSlot()
    def buyBatch2(self):
        ret = QMessageBox.warning(self.mainwindow,
                u"",
                u"<H3>确认买入股票组合？（买入档位：<FONT COLOR='#FF0000'>%s</FONT>，价格修正：<FONT COLOR='#FF0000'>%s</FONT>）</H3>"
                % (self.portfolio.pricepolicynamemap[self.portfolio.buypolicy],
                    self.portfolio.buypricefix),
                QMessageBox.Ok|QMessageBox.Cancel)
        if QMessageBox.Ok == ret:
            # self.portfolio.pricepolicynamemap[self.portfolio.buypolicy], self.buypricefix
            self.portfolio.buyBatch2()

    @pyqtSlot()
    def buyBatch_r(self):
        # _r for remote call from controller
        self.portfolio.buyBatch()

    @pyqtSlot()
    def buyBatch2_r(self):
        # _r for remote call from controller
        self.portfolio.buyBatch2()

    @pyqtSlot()
    def cancelBuyBatch(self):
        #ret = QMessageBox.warning(self.mainwindow,
        #        u"", u"<H3>确认<FONT COLOR='#FF0000'>撤销买入</FONT>？</H3>",
        #        QMessageBox.Ok|QMessageBox.Cancel)
        if True:#QMessageBox.Ok == ret:
            self.portfolio.cancelBuyBatch()

    @pyqtSlot()
    def sellBatch(self):
        ret = QMessageBox.warning(self.mainwindow,
                u"",
                u"<H3>确认卖出股票组合？（卖出档位：<FONT COLOR='#FF0000'>%s</FONT>，价格修正：<FONT COLOR='#FF0000'>%s</FONT>）</H3>"
                % (self.portfolio.pricepolicynamemap[self.portfolio.sellpolicy],
                    self.portfolio.sellpricefix),
                QMessageBox.Ok|QMessageBox.Cancel)
        if QMessageBox.Ok == ret:
            self.portfolio.sellBatch()

    @pyqtSlot()
    def sellBatch2(self):
        ret = QMessageBox.warning(self.mainwindow,
                u"",
                u"<H3>确认卖出股票组合？（卖出档位：<FONT COLOR='#FF0000'>%s</FONT>，价格修正：<FONT COLOR='#FF0000'>%s</FONT>）</H3>"
                % (self.portfolio.pricepolicynamemap[self.portfolio.sellpolicy],
                    self.portfolio.sellpricefix),
                QMessageBox.Ok|QMessageBox.Cancel)
        if QMessageBox.Ok == ret:
            self.portfolio.sellBatch2()

    @pyqtSlot()
    def sellBatch_r(self):
        self.portfolio.sellBatch()

    @pyqtSlot()
    def sellBatch2_r(self):
        self.portfolio.sellBatch2()

    @pyqtSlot()
    def cancelSellBatch(self):
        #ret = QMessageBox.warning(self.mainwindow,
        #        u"", u"<H3>确认<FONT COLOR='#FF0000'>撤销卖出</FONT>？</H3>",
        #        QMessageBox.Ok|QMessageBox.Cancel)
        if True:#QMessageBox.Ok == ret:
            self.portfolio.cancelSellBatch()

    @pyqtSlot()
    def openshort(self):
        ret = QMessageBox.warning(self.mainwindow,
                u"",
                u"<H3>确认股指期货建仓？（建仓档位：<FONT COLOR='#FF0000'>%s</FONT>，点数修正：<FONT COLOR='#FF0000'>%s</FONT>）</H3>"
                % (self.portfolio.pricepolicynamemap[self.portfolio.openpolicy],
                    self.portfolio.openpricefix),
                QMessageBox.Ok|QMessageBox.Cancel)
        if QMessageBox.Ok == ret:
            self.portfolio.openshort()
            QMetaObject.invokeMethod(self.sindexmodel, "updaterow", Qt.QueuedConnection)
            self.savePortfolio()

    @pyqtSlot()
    def openshort_r(self):
        self.portfolio.openshort()
        QMetaObject.invokeMethod(self.sindexmodel, "updaterow", Qt.QueuedConnection)
        self.savePortfolio()

    @pyqtSlot()
    def cancelopen(self):
        #ret = QMessageBox.warning(self.mainwindow,
        #        u"", u"<H3>确认<FONT COLOR='#FF0000'>取消建仓</FONT>？</H3>",
        #        QMessageBox.Ok|QMessageBox.Cancel)
        if True:#QMessageBox.Ok == ret:
            self.portfolio.cancelopenshort()
            QMetaObject.invokeMethod(self.sindexmodel, "updaterow", Qt.QueuedConnection)
            self.savePortfolio()

    @pyqtSlot()
    def closeshort(self):
        ret = QMessageBox.warning(self.mainwindow,
                u"",
                u"<H3>确认股指期货平仓？（平仓档位：<FONT COLOR='#FF0000'>%s</FONT>，点数修正：<FONT COLOR='#FF0000'>%s</FONT>）</H3>"
                % (self.portfolio.pricepolicynamemap[self.portfolio.closepolicy],
                    self.portfolio.closepricefix),
                QMessageBox.Ok|QMessageBox.Cancel)
        if QMessageBox.Ok == ret:
            self.portfolio.closeshort()
            QMetaObject.invokeMethod(self.sindexmodel, "updaterow", Qt.QueuedConnection)
            self.savePortfolio()

    @pyqtSlot()
    def closeshort_r(self):
        self.portfolio.closeshort()
        QMetaObject.invokeMethod(self.sindexmodel, "updaterow", Qt.QueuedConnection)
        self.savePortfolio()

    @pyqtSlot()
    def cancelclose(self):
        #ret = QMessageBox.warning(self.mainwindow,
        #        u"", u"<H3>确认<FONT COLOR='#FF0000'>取消平仓</FONT>？</H3>",
        #        QMessageBox.Ok|QMessageBox.Cancel)
        if True:#QMessageBox.Ok == ret:
            self.portfolio.cancelcloseshort()
            QMetaObject.invokeMethod(self.sindexmodel, "updaterow", Qt.QueuedConnection)
            self.savePortfolio()

    @pyqtSlot()
    def sifsubmit(self):
        code = self.portfolio.sindexinfo["code"]
        share = str(self.sifnumspin.value())
        if self.sifosrad.isChecked():
            openclose = "open"
            longshort = "short"
            optxt = u"空开"
            price = "%0.1f" % self.portfolio.sindexinfo["openposprice"]
        elif self.sifcsrad.isChecked():
            openclose = "close"
            longshort = "short"
            optxt = u"空平"
            price = "%0.1f" % self.portfolio.sindexinfo["closeposprice"]
        elif self.sifolrad.isChecked():
            openclose = "open"
            longshort = "long"
            optxt = u"多开"
            price = "%0.1f" % self.portfolio.sindexinfo["openposprice"]
        elif self.sifclrad.isChecked():
            openclose = "close"
            longshort = "long"
            optxt = u"多平"
            price = "%0.1f" % self.portfolio.sindexinfo["closeposprice"]
        else:
            QMessageBox.warning(self.mainwindow,
                    u"",
                    u"未选操作",
                    QMessageBox.Ok)
            return

        ret = QMessageBox.warning(self.mainwindow,
                u"",
                u"<H3>确认%s？\n代码：%s\n价格：%s\n数量：%s</H3>"
                % (optxt, code, price, share),
                QMessageBox.Ok|QMessageBox.Cancel)
        if QMessageBox.Ok == ret:
            sioinf = self.portfolio.makesiforder(code, price, share, openclose, longshort)
            self.portfolio.sifquickinfo = sioinf
            QMetaObject.invokeMethod(self.sifocntline, "setText",
                    Qt.QueuedConnection,
                    Q_ARG("QString",
                        QString(share)))
            QMetaObject.invokeMethod(self.sifdcntline, "setText",
                    Qt.QueuedConnection,
                    Q_ARG("QString",
                        QString("")))
            if sioinf["order_id"] == "":
                QMetaObject.invokeMethod(self.sifstatusline, "setText",
                        Qt.QueuedConnection,
                        Q_ARG("QString",
                            QString(u"委托失败: %s"%sioinf["failinfo"])))
                QMetaObject.invokeMethod(self.sifoidline, "setText",
                        Qt.QueuedConnection,
                        Q_ARG("QString",
                            QString("")))
            else:
                QMetaObject.invokeMethod(self.sifoidline, "setText",
                        Qt.QueuedConnection,
                        Q_ARG("QString",
                            QString(sioinf["order_id"])))
                QMetaObject.invokeMethod(self.sifstatusline, "setText",
                        Qt.QueuedConnection,
                        Q_ARG("QString",
                            QString(u"委托成功")))

    @pyqtSlot()
    def sifcancel(self):
        if self.portfolio.sifquickinfo["order_id"]:
            sirec = self.portfolio.sifquickinfo
            cancelcount = int(sirec["ordercount"]) - int(sirec["dealcount"]) 
            if cancelcount != 0:
                resp = self.portfolio.cancelsiforder(sirec, str(cancelcount))
                if resp.records[0][0] == "Y":
                    QMetaObject.invokeMethod(self.sifstatusline, "setText",
                            Qt.QueuedConnection,
                            Q_ARG("QString",
                                QString(u"撤单成功")))
                else:
                    QMetaObject.invokeMethod(self.sifstatusline, "setText",
                            Qt.QueuedConnection,
                            Q_ARG("QString",
                                QString(u"撤单失败: %s"%resp.failinfo)))

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

    @pyqtSlot(int)
    def setforcecancelbuy(self, state):
        self.portfolio.forcecancelbuy = self.forcecancelbuychk.isChecked()

    @pyqtSlot(int)
    def setforcecancelsell(self, state):
        self.portfolio.forcecancelsell = self.forcecancelsellchk.isChecked()

    @pyqtSlot()
    def showstockinfo(self):
        sqdlg = stockquerydlg(self.session_cfg)
        if sqdlg.setup():
            sqdlg.show()
            sqdlg.activateWindow()
            QMetaObject.invokeMethod(sqdlg.refresh, "clicked", Qt.QueuedConnection)
            sqdlg.exec_()
        else:
            QMessageBox.information(self.mainwindow, "", u"不能登录")

    @pyqtSlot()
    def showposstat(self):
        pidlg = positioninfodlg(self.portfolio)
        pidlg.setup()
        QMetaObject.invokeMethod(pidlg.refresh, "clicked", Qt.QueuedConnection)
        pidlg.show()
        pidlg.activateWindow()
        pidlg.exec_()

    @pyqtSlot()
    def genbuyfromsell(self):
        # check that bostate is in sell or cancelsell
        if self.portfolio.bostate not in [Portfolio.BOSELLSUCCESS, Portfolio.BOSELLCANCELED]:
            QMessageBox.information(self.mainwindow, "", u"尚未卖出")
            return

        # check that every stock is selled compeletly or canceled
        oktogo = True
        for scode in self.portfolio.stocklist:
            si = self.portfolio.stockinfo[scode]
            if len(si["pastsell"]) > 0:
                od = si["pastsell"][-1]
                if od["order_state"] == Portfolio.CANCELSELLSUCCESS:
                    pass
                elif od["order_state"] == Portfolio.CANCELSELLWAIT:
                    QMessageBox.information(self.mainwindow, "",
                            u"失败：卖出等成交(%s)" % scode)
                    oktogo = False
                    break
                elif od["order_state"] == Portfolio.SELLSUCCESS:
                    if od["ordercount"] != od["dealcount"]:
                        QMessageBox.information(self.mainwindow, "",
                                u"失败：正在卖出(%s)，先强撤" % scode)
                        oktogo = False
                        break

        if not oktogo:
            return

        # ask for saved ptf file location and save it.
        # for each stock, gen buy count as selled number rounded to 100
        ptffn = QFileDialog.getSaveFileName(self, u"", u"", u"*.ptf")
        if ptffn == "":
            return
        try:
            f = open(ptffn, "wb")
            writer = csv.writer(f)
            for scode in self.portfolio.stocklist:
                si = self.portfolio.stockinfo[scode]

                mkt = si["market"]
                code = si["code"]
                count = si["currentsellcount"]
                if int(count) < 50:
                    continue

                pastbuy = []
                pastsell = []

                writer.writerow([mkt, code, count,
                    repr(pastbuy), repr(pastsell)])
            f.flush()
            f.close()
        except IOError:
            QMessageBox.information(None, "", u"不能保存组合.")

    def showbostate(self):
        QMetaObject.invokeMethod(self.bostatusline, "setText",
                Qt.QueuedConnection,
                Q_ARG("QString",
                    QString(self.portfolio.bostate)))

    @pyqtSlot()
    def on_loadlogbtn_clicked(self):
        logs = open(self.portfolio.logfn, "r").read()
        try:
            self.logtext.setPlainText(logs.decode("utf8"))
        except UnicodeError:
            self.logtext.setPlainText(logs)

    @pyqtSlot()
    def warnbatchfailed(self):
        QMessageBox.warning(None,
                u"",
                u"<FONT COLOR='#FF0000'>存在批量失败</FONT>",
                QMessageBox.Ok)

class basediffUpdater(Thread):
    def __init__(self, pupdter, jsdcfg, uic, pstat):
        Thread.__init__(self)
        self.runflag = True

        self.jsdcfg = jsdcfg
        self.jsdsession = None
        self.uic = uic
        self.pupdter = pupdter
        self.pstat = pstat
        self.hs300code = "SH000300"
        self.pupdter.addhook(self.hs300code)

        self.m_media = Phonon.MediaObject(self.uic.mainwindow)
        audioOutput = Phonon.AudioOutput(Phonon.MusicCategory,
                self.uic.mainwindow)
        Phonon.createPath(self.m_media, audioOutput)

        self.m_media2 = Phonon.MediaObject(self.uic.mainwindow)
        audioOutput2 = Phonon.AudioOutput(Phonon.MusicCategory,
                self.uic.mainwindow)
        Phonon.createPath(self.m_media2, audioOutput2)

        self.playsignal = self.uic.playsignalchk.isChecked()
        self.uic.mainwindow.connect(self.uic.playsignalchk, SIGNAL("stateChanged(int)"), self.setplay)
        self.uic.mainwindow.connect(self.m_media, SIGNAL("aboutToFinish()"), self.addsong)
        self.uic.mainwindow.connect(self.m_media2, SIGNAL("aboutToFinish()"), self.addsong2)

        self.opendir = u"openmusic"
        self.closedir = u"closemusic"
        self.openmusic = glob.glob(os.path.join(self.opendir, "*.mp3"))
        self.closemusic = glob.glob(os.path.join(self.closedir, "*.mp3"))
        musicfn = random.choice(self.openmusic)
        self.m_media.setCurrentSource(Phonon.MediaSource(musicfn))
        musicfn = random.choice(self.closemusic)
        self.m_media2.setCurrentSource(Phonon.MediaSource(musicfn))

        self.name = self.__class__.__name__
        self.logger = logging.getLogger()

    def run(self):
        try:

            self.jsdsession = jsd.session(self.jsdcfg)
            if not self.jsdsession.setup():
                self.logger.warning("jsd session setup failed.")
                return
            
            self.sicontracts = calsicontracts()
            for sindex in self.sicontracts:
                self.uic.sindexcmbox.addItem(sindex)
            self.uic.sindexcmbox.setCurrentIndex(0)

            while self.runflag:
                time.sleep(1)
                # update hs300
                rec = self.pupdter.gethookquote(self.hs300code)
                if rec is None:
                    continue

                hs300latest = rec['S8']

                # update selected stock index
                # TODO: use hq pushee
                hqreq = jsd.QueryHQReq(self.jsdsession)
                hqreq["exchcode"] = self.jsdsession["cffexcode"]
                hqreq["code"] = self.sicontracts[self.uic.sindexcmbox.currentIndex()]
                hqreq.send()
                hqresp = jsd.QueryHQResp(self.jsdsession)
                hqresp.recv()
                if hqresp.anwser == "N":
                    continue
                silatest = float(hqresp.records[0][9])

                # calculate basediff
                basediff = silatest - hs300latest
                basediffper = basediff / hs300latest * 100
                self.pstat["basediff"] = basediff
                self.pstat["basediffper"] = basediffper

                # update UI
                QMetaObject.invokeMethod(self.uic.hs300line, "setText", Qt.QueuedConnection,
                        Q_ARG("QString", QString(str(hs300latest))))
                QMetaObject.invokeMethod(self.uic.sindexline, "setText", Qt.QueuedConnection,
                        Q_ARG("QString", QString(str(silatest))))
                QMetaObject.invokeMethod(self.uic.basediffline, "setText", Qt.QueuedConnection,
                        Q_ARG("QString", QString(str(basediff))))
                QMetaObject.invokeMethod(self.uic.basediffperline, "setText", Qt.QueuedConnection,
                        Q_ARG("QString", QString(str("%.3f" % basediffper))))

                #self.uic.hs300line.setText(str(hs300latest))
                #self.uic.sindexline.setText(str(silatest))
                #self.uic.basediffline.setText(str(basediff))
                #self.uic.basediffperline.setText("%.3f" % basediffper)
                openthreshold = self.uic.openthresholdspin.value()
                if basediffper >= openthreshold:
                    QMetaObject.invokeMethod(self.uic.openthresholdspin, "setStyleSheet",
                            Qt.QueuedConnection, Q_ARG("QString", QString(str("background-color: rgb(255, 0, 0);"))))
                    self.play()
                else:
                    QMetaObject.invokeMethod(self.uic.openthresholdspin, "setStyleSheet",
                            Qt.QueuedConnection, Q_ARG("QString", QString(str("background-color: rgb(255, 255, 255);"))))
                    self.stopplay()

                closethreshold = self.uic.closethresholdspin.value()
                if basediffper <= closethreshold:
                    QMetaObject.invokeMethod(self.uic.closethresholdspin, "setStyleSheet",
                            Qt.QueuedConnection, Q_ARG("QString", QString(str("background-color: rgb(255, 0, 0);"))))
                    self.play2()
                else:
                    QMetaObject.invokeMethod(self.uic.closethresholdspin, "setStyleSheet",
                            Qt.QueuedConnection, Q_ARG("QString", QString(str("background-color: rgb(255, 255, 255);"))))
                    self.stopplay2()

        except Exception:
            self.logger.exception("Oh!!!")

    def stop(self):
        self.runflag = False
        self.stopplay()
        self.stopplay2()

    @pyqtSlot(int)
    def setplay(self, state):
        self.playsignal = self.uic.playsignalchk.isChecked()
        if not self.playsignal:
            self.stopplay()
            self.stopplay2()

    @pyqtSlot()
    def addsong(self):
        musicfn = random.choice(self.openmusic)
        self.m_media.enqueue(Phonon.MediaSource(musicfn))

    @pyqtSlot()
    def addsong2(self):
        musicfn = random.choice(self.closemusic)
        self.m_media2.enqueue(Phonon.MediaSource(musicfn))

    @pyqtSlot()
    def play(self):
        if self.playsignal:
            self.m_media.play()

    @pyqtSlot()
    def play2(self):
        if self.playsignal:
            self.m_media2.play()

    @pyqtSlot()
    def stopplay(self):
        self.m_media.pause()

    @pyqtSlot()
    def stopplay2(self):
        self.m_media2.pause()

def testslot(t):
    print t

def verifymap(dbfn, mapfn, codekey):
    try:
        db = dbf.Dbf(dbfn, ignoreErrors=True, readOnly=True)
        f = open(mapfn)
    except IOError, e:
        logging.getLogger().exception("cannot find file.")
        return False

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

def incmonth(yearmonth, inc=1):
    # yearmonth is a (year, month) tuple
    year, month = yearmonth
    for i in range(inc):
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
    return (year, month)

def calsicontracts():
    # if today <= deliver data: this month, next month, next quarter, n-next quarter
    # else: next month, next next month, ...
    today = date.today()
    deliverday = date(today.year, today.month, 1)
    oneday = timedelta(1)
    fridaycount = 0
    contracts = []
    while deliverday < today:
        if deliverday.isoweekday() == 5:
            fridaycount += 1
        deliverday += oneday
    contract = (today.year, today.month)
    if fridaycount >= 3:
        contract = incmonth(contract)

    contracts.append(contract)
    contract = incmonth(contract)
    contracts.append(contract)

    for i in range(2):
        while 1:
            contract = incmonth(contract)
            if contract[1] % 3 == 0:
                contracts.append(contract)
                break
    return [ "".join(("IF", str(year)[2:], "%02d"%month)) for (year, month) in contracts]
