# -*- coding: utf-8 -*-

import sys
import socket
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from tradeui import Ui_MainWindow
from dbfpy import dbf
from threading import Thread
import time
import shutil
import types
import jz

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

    def __init__(self, stockbatch, s):
        # market code (SH, SZ), stock number, count
        self.session = s
        self.stocklist = []
        self.stockset = set()
        self.stockattr = ["count", "market", "code", "name", "latestprice", "buyprice", "sellprice", "order_id", "orderedcount", "orderprice", "dealcount", "dealprice"]
        self.stockmodelattr = ["count", "market", "code", "name", "orderedcount", "dealcount", "orderprice", "dealprice", "latestprice", "buyprice", "sellprice"]
        # use market+stock number as key
        self.dealrecord = {}
        self.stockinfo = {}
        for i in stockbatch:
            scode = i[0].upper() + i[1]
            self.stocklist.append(scode)
            self.stockinfo.setdefault(scode, {})
            self.dealrecord.setdefault(scode, {})

            self.stockinfo[scode]["count"] = i[2]
            self.stockinfo[scode]["market"] = i[0].upper()
            self.stockinfo[scode]["code"] = i[1]
            self.stockinfo[scode]["order_id"] = ""

            self.stockset = set(self.stocklist)

    @staticmethod
    def readBatchOrder(bofn):
        # bofn specifies batch order in lines, each lines contains
        # market code (SH, SZ), stock number, count
        # separated by spaces
        # return: batch orders in a list, and bad lines
        bo = []
        badlines = []
        f = open(bofn)
        for line in f:
            if line == "": # EOF
                break

            boitem = line.split()
            if len(boitem) != 3: # empty line or others
                if line != "\n":
                    badlines.append(line.strip())
                continue

            if( (boitem[0].upper()!="SH" and boitem[0].upper()!="SZ") or (int(boitem[2])%100 != 0) ):
                badlines.append(line.strip())
                continue

            bo.append(boitem)
        f.close()
        return (bo, badlines)

    @staticmethod
    def readportfolio(fn):
        stocklist = []
        stockcount = []
        f=open(fn)
        for line in f:
            s, c = line.split()
            stocklist.append(s)
            stockcount.append(int(c))
        f.close()
        assert(len(stocklist) == len(stockcount))
        return stocklist, stockcount

    def batchOrderSubmit(self):
        # return:

        # submit first order item, use its order_id as following orders' biz_no
        scode = self.stocklist[0]
        req = SubmitOrderReq(s)
        req["user_code"] = s["user_code"]
        if self.stockinfo[scode]["market"] == "SH":
            req["market"] = "10"
            req["secu_acc"] = s["secu_acc"]["SH"]
        elif self.stockinfo[scode]["market"] == "SZ":
            req["market"] = "00"
            req["secu_acc"] = s["secu_acc"]["SZ"]
        req["account"] = s["account"] # capital account
        req["secu_code"] = self.stockinfo[scode]["code"]
        req["trd_id"] = "0B" # TODO: buy method
        req["price"] = "?" # TODO: buy price
        req["qty"] = self.stockinfo[scode]["count"]
        req.send()
        resp = SubmitOrderResp(s)
        resp.recv()
        s.storetrade(req.payload, resp.payload)
        if resp.retcode == "0":
            # TODO: handle error message
            self.stockinfo[scode]["order_id"] = resp.records[0][1]

        first_order_id = resp.records[0][1]
        # submit following itmes.
        for scode in self.stocklist[1:]:
            req = SubmitOrderReq(s)
            req["user_code"] = s["user_code"]
            if self.stockinfo[scode]["market"] == "SH":
                req["market"] = "10"
                req["secu_acc"] = s["secu_acc"]["SH"]
            elif self.stockinfo[scode]["market"] == "SZ":
                req["market"] = "00"
                req["secu_acc"] = s["secu_acc"]["SZ"]
            req["account"] = s["account"]
            req["secu_code"] = self.stockinfo[scode]["code"]
            req["trd_id"] = "0B"
            req["price"] = "?"
            req["qty"] = self.stockinfo[scode]["count"]
            req["biz_no"] = first_order_id
            req.send()
            resp = SubmitOrderResp(s)
            resp.recv()
            s.storetrade(req.payload, resp.payload)
            if resp.retcode == "0":
                self.stockinfo[scode]["order_id"] = resp.records[0][1]

class PortfolioUpdater(Thread):
    def __init__(self, shdbfn, szdbfn, portfolio, portmodel):
        Thread.__init__(self)
        self.shdbfn = shdbfn
        self.szdbfn = szdbfn
        self.portfolio = portfolio
        self.portmodel = portmodel
        self.runflag = True
        self.localshdbfn = "show2003.local.et"
        self.localszdbfn = "sjshq.local.et"

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

    def update(self):
        # show2003 only considers SH market
        shutil.copy(self.shdbfn, self.localshdbfn)
        shutil.copy(self.szdbfn, self.localszdbfn)
        dbsh = dbf.Dbf(self.localshdbfn, ignoreErrors=True, readOnly=True)
        dbsz = dbf.Dbf(self.localszdbfn, ignoreErrors=True, readOnly=True)

        # update SH stock
        for s in dbsh:
            # a dirty patch
            scode = "SH" + s[0]
            if scode in self.portfolio.stockset:
                stockinfo = self.portfolio.stockinfo[scode]
                for f in self.shdbfield:
                    if type(s[f]) is types.StringType:
                        stockinfo[self.shdbmapping[f]] = s[f].decode("GBK")
                    else:
                        stockinfo[self.shdbmapping[f]] = s[f]
        dbsh.close()

        # update SZ stock
        for s in dbsz:
            # a dirty patch
            scode = "SZ" + s[0]
            if scode in self.portfolio.stockset:
                stockinfo = self.portfolio.stockinfo[scode]
                for f in self.szdbfield:
                    if type(s[f]) is types.StringType:
                        stockinfo[self.szdbmapping[f]] = s[f].decode("GBK")
                    else:
                        stockinfo[self.szdbmapping[f]] = s[f]
        dbsz.close()

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
    def __init__(self, portfolio, portmodel):
        Thread.__init__(self)
        self.portfolio = portfolio
        self.portmodel = portmodel
        self.runflag = True
        self.session = portfolio.session

    def update(self):
        for scode in self.portfolio.stocklist:
            if self.portfolio.stockinfo[scode]["order_id"] != "":
                qoreq = jz.QueryOrderReq(self.session)
                qoreq["user_code"] = self.session["user_code"]
                if self.portfolio.stockinfo[scode]["market"] == "SH":
                    qoreq["market"] = "10"
                elif self.portfolio.stockinfo[scode]["market"] == "SZ":
                    qoreq["market"] = "00"
                qoreq["order_id"] = self.portfolio.stockinfo[scode]["order_id"]
                qoreq.send()
                qoresp = jz.QueryOrderResp(self.session)
                qoresp.recv()
                if qoresp.retcode == "0":
                    pass
                # TODO: update deal info

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

def openfile():
    fn = QFileDialog.getOpenFileName()
    return fn

def main(args):
    app = QApplication(args)
    window = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(window)

    # read config
    shdbfn = "z:\\show2003.dbf"
    szdbfn = "z:\\sjshq.dbf"
    tradedbfn = "tradeinfo.db"
    portfoliofn = "hs300.txt"

    jzserver = "172.18.20.52"
    jzport = 9100
    jzaccount = "85804530"
    jzaccounttype = "Z"
    jzpasswd = "123444"

    # setup session and login jinzheng
    # TODO: handle login error
    conn = socket.socket()
    conn.connect((jzserver, jzport))

    mysession = jz.session(conn, tradedbfn)
    cireq = jz.CheckinReq(mysession)
    cireq.send()
    ciresp = jz.CheckinResp(mysession)
    ciresp.recv()
    # update workkey
    mysession["workkey"] = ciresp.getworkkey()

    loginreq = jz.LoginReq(mysession)
    loginreq["idtype"] = jzaccounttype
    loginreq["id"] = jzaccount
    loginreq["passwd"] = mysession.encrypt(jz.pad(jzpasswd, (len(jzpasswd)/8+1)*8))
    loginreq.send()
    loginresp = jz.LoginResp(mysession)
    loginresp.recv()
    # update session fields from login response
    if loginresp.retcode == "0":
        loginresp.updatesession()
        print "Login ok"

    # setup portfolio
    bo, badlines = Portfolio.readBatchOrder(portfoliofn)
    if len(badlines) > 0:
        print "There're bad lines."
        print badlines
    p = Portfolio(bo, mysession)

    # setup portfolio model for showing in table
    pmodel = PortfolioModel(p)
    ui.stock.setModel(pmodel)

    # run the portfolio updater
    pupdater = PortfolioUpdater(shdbfn, szdbfn, p, pmodel)
    pupdater.start()

    # run the order info updater
    orderupdater = OrderUpdater(p, pmodel)
    orderupdater.start()

    # setup menu
    window.connect(ui.import_portfolio, SIGNAL("activated()"), openfile)

    window.show()
    app.exec_()
    pupdater.stop()
    orderupdater.stop()
    mysession.close()

if __name__=="__main__":
    main(sys.argv)
