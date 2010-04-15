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
    UNORDERED = 0
    ORDERED   = 2
    ORDERFAILED = 3
    ORDERSUCCESS = 4
    # assumption: only success order can be canceled
    CANCELSUCCESS = 5
    CANCELFAILED = 6


    def __init__(self, stockbatch, sessioncfg):
        # market code (SH, SZ), stock number, count
        self.session = jz.session(sessioncfg)
        if not self.session.setup():
            print "session setup failed."
            sys.exit(1)

        self.stocklist = []
        self.stockset = set()
        self.stockattr = ["count", "market", "code", "name", "latestprice",
                "buyprice", "sellprice", "order_id", "order_date", "order_time",
                "orderedcount", "orderprice", "dealcount", "dealprice", "state",
                "cancel_date", "cancel_time"]
        self.stockmodelattr = ["count", "market", "code", "name", "order_date",
                "order_time", "orderedcount", "dealcount", "orderprice",
                "dealprice", "latestprice", "cancel_date", "cancel_time"]
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
            self.stockinfo[scode]["order_id"] = ""
            self.stockinfo[scode]["order_date"] = ""
            self.stockinfo[scode]["order_time"] = ""
            try:
                self.stockinfo[scode]["order_id"] = i[3]
                self.stockinfo[scode]["order_date"] = i[4]
                self.stockinfo[scode]["order_time"] = i[5]
            except IndexError:
                pass
        self.stockset = set(self.stocklist)

        # can be derived from stock state?
        self.batchstate = Portfolio.UNORDERED
        for s in self.stocklist:
            self.stockinfo[s]["state"] = Portfolio.UNORDERED

    def __del__(self):
        self.session.close()

    @staticmethod
    def readBatchOrder(bofn):
        # bofn specifies batch order in lines, each lines contains
        # market code (SH, SZ), stock number, count and order_id, order_date, order_time
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
            f.write(" ".join( (si["market"], si["code"], si["count"], si["order_id"], si["order_date"], si["order_time"]) ))
            f.write("\n")
        f.flush()
        f.close()

    def submitBatchOrder(self, trdid):
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

        #today = str(datetime.today().date())
        #scode = self.stocklist[0]
        #req = jz.SubmitOrderReq(self.session)
        #req["user_code"] = self.session["user_code"]
        #if self.stockinfo[scode]["market"] == "SH":
        #    req["market"] = "10"
        #    req["secu_acc"] = self.session["secu_acc"]["SH"]
        #elif self.stockinfo[scode]["market"] == "SZ":
        #    req["market"] = "00"
        #    req["secu_acc"] = self.session["secu_acc"]["SZ"]
        #req["account"] = self.session["account"] # capital account
        #req["secu_code"] = self.stockinfo[scode]["code"]
        #req["trd_id"] = trdcode
        #req["price"] = self.stockinfo[scode]["orderprice"]
        #req["qty"] = self.stockinfo[scode]["count"]
        #req.send()
        #resp = jz.SubmitOrderResp(self.session)
        #resp.recv()
        #self.session.storetrade(req.payload, resp.payload)
        #if resp.retcode == "0":
        #    # TODO: handle error message
        #    self.stockinfo[scode]["order_id"] = resp.records[0][1]
        #    self.stockinfo[scode]["order_date"] = today
        #    self.stockinfo[scode]["order_time"] = str(datetime.now().time())

        #first_order_id = ""
        today = str(datetime.today().date())
        for scode in self.stocklist:
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
                self.stockinfo[scode]["state"] = Portfolio.ORDERSUCCESS
            else:
                self.stockinfo[scode]["state"] = Portfolio.ORDERFAILED

            #    if first_order_id == "":
            #        first_order_id = resp.records[0][1]

    def cancelBatchOrder(self):
        # only success orders can be canceled
        today = str(datetime.today().date())
        for scode in self.stocklist:
            if self.stockinfo[scode]["state"] == Portfolio.ORDERSUCCESS:
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
                    self.stockinfo[scode]["state"] = Portfolio.CANCELSUCCESS
                    self.stockinfo[scode]["cancel_date"] = today
                    self.stockinfo[scode]["cancel_time"] = str(datetime.now().time())
                else:
                    self.stockinfo[scode]["state"] = Portfolio.CANCELFAILED

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
                # update order price for SH
                stockinfo["orderprice"] = self.getpricesh(s, self.portfolio.pricepolicy)
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
                # update order price for SZ
                stockinfo["orderprice"] = self.getpricesz(s, self.portfolio.pricepolicy)
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

def openfile():
    fn = QFileDialog.getOpenFileName()
    return fn

def testslot(t):
    print t

def main(args):
    app = QApplication(args)
    window = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(window)

    # read config
    shdbfn = "z:\\show2003.dbf"
    szdbfn = "z:\\sjshq.dbf"
    #portfoliofn = "hs300.txt"
    portfoliofn = openfile()

    session_config = {}
    session_config["tradedbfn"] = "tradeinfo.db"
    session_config["jzserver"] = "172.18.20.52"
    session_config["jzport"] = 9100
    session_config["jzaccount"] = "85804530"
    session_config["jzaccounttype"] = "Z"
    session_config["jzpasswd"] = "123444"

    # setup session and login jinzheng
    # TODO: handle login error
    #conn = socket.socket()
    #conn.connect((jzserver, jzport))

    #mysession = jz.session(session_config)
    #cireq = jz.CheckinReq(mysession)
    #cireq.send()
    #ciresp = jz.CheckinResp(mysession)
    #ciresp.recv()
    ## update workkey
    #mysession["workkey"] = ciresp.getworkkey()

    #loginreq = jz.LoginReq(mysession)
    #loginreq["idtype"] = jzaccounttype
    #loginreq["id"] = jzaccount
    #loginreq["passwd"] = mysession.encrypt(jz.pad(jzpasswd, (len(jzpasswd)/8+1)*8))
    #loginreq.send()
    #loginresp = jz.LoginResp(mysession)
    #loginresp.recv()
    ## update session fields from login response
    #if loginresp.retcode == "0":
    #    loginresp.updatesession()
    #    print "Login ok"

    # setup portfolio
    bo, badlines = Portfolio.readBatchOrder(portfoliofn)
    if len(badlines) > 0:
        print "There're bad lines."
        print badlines
    p = Portfolio(bo, session_config)

    # setup portfolio model for showing in table
    pmodel = PortfolioModel(p)
    ui.stock.setModel(pmodel)

    # run the portfolio updater
    pupdater = PortfolioUpdater(shdbfn, szdbfn, p, pmodel)
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

