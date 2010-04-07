# -*- coding: utf-8 -*-

import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from tradeui import Ui_MainWindow
from dbfpy import dbf
from threading import Thread
import time
import shutil
import types

class PortfolioModel(QAbstractTableModel):
    def __init__(self, portfolio, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.portfolio = portfolio

    def rowCount(self, parent):
        return len(self.portfolio.stocklist)

    def columnCount(self, parent):
        return len(self.portfolio.stockattr)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.portfolio.stockattr[section])
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return QVariant(str(section + 1))
        return QVariant()

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        rowkey = self.portfolio.stocklist[index.row()]
        columnkey = self.portfolio.stockattr[index.column()]
        try:
            celldata = self.portfolio.data[rowkey][columnkey]
            return QVariant(celldata)
        except KeyError:
            return QVariant()

class Portfolio:
    def __init__(self, stocklist, stockcount):
        # list is stock id
        self.stocklist = stocklist
        self.stockattr = ["count", "code", "name", "latest", "buy", "sell"]
        self.stockset = set(stocklist)
        self.stockcount = stockcount
        self.data = {}
        for i in range(len(self.stocklist)):
            s = self.stocklist[i]
            self.data.setdefault(s, {})
            self.data[s]["code"] = s
            self.data[s]["count"] = self.stockcount[i]

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

class PortfolioUpdater(Thread):
    def __init__(self, dbfn, portfolio, portmodel):
        Thread.__init__(self)
        self.dbfn = dbfn
        self.portfolio = portfolio
        self.portmodel = portmodel
        self.runflag = True
        self.localdbfn = "show2003.local.et"

        # one-to-one mapping of dbfield to stockattr
        self.dbfield = ["S1", "S2", "S8", "S9", "S10"]
        self.dbmapping = {
                "S1":"code",
                "S2":"name",
                "S8":"latest",
                "S9":"buy",
                "S10":"sell"
                }
        assert(len(self.dbfield) == len(self.dbmapping))

    def update(self):#dbfn, stockdata, stocklist, model):
        shutil.copy(self.dbfn, self.localdbfn)
        db = dbf.Dbf(self.localdbfn, ignoreErrors=True, readOnly=True)
        for s in db:
            if s[0] in self.portfolio.stockset:
                stockdata = self.portfolio.data[s[0]]
                for f in self.dbfield:
                    if type(s[f]) is types.StringType:
                        stockdata[self.dbmapping[f]] = s[f].decode("GBK")
                    else:
                        stockdata[self.dbmapping[f]] = s[f]
        db.close()
        self.portmodel.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                self.portmodel.index(0,0), self.portmodel.index(
                    len(self.portfolio.data)-1,
                    len(self.portfolio.stockattr)-1))

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
    dbfn = "z:\show2003.dbf"
    portfoliofn = "hs300.txt"

    # setup session and login jinzheng
    jzserver = "172.18.20.52"
    jzport = 9100
    jzaccount = "85804530"
    jzaccounttype = "Z"
    jzpasswd = "123444"

    # setup portfolio
    list, count = Portfolio.readportfolio(portfoliofn)
    p = Portfolio(list, count)

    # setup portfolio model for showing in table
    pmodel = PortfolioModel(p)
    ui.stock.setModel(pmodel)

    # run the portfolio updater
    pupdater = PortfolioUpdater(dbfn, p, pmodel)
    pupdater.start()

    # setup menu
    window.connect(ui.import_portfolio, SIGNAL("activated()"), openfile)

    window.show()
    app.exec_()
    pupdater.stop()

if __name__=="__main__":
    main(sys.argv)

