# -*- coding: utf-8 -*-
import sys
from positioninfoui import Ui_positioninfodlg
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class positioninfodlg(QDialog, Ui_positioninfodlg):
    def __init__(self, portfolio):
        QDialog.__init__(self)
        self.portfolio = portfolio

    @pyqtSlot()
    def on_refresh_clicked(self):
        totalcost = 0
        mktval = 0
        for scode in self.portfolio.stockinfo:
            si = self.portfolio.stockinfo[scode]
            totalcost = totalcost + si["currentbuycost"]
            mktval = mktval + si["currentbuycount"] * float(si["latestprice"])
        profitval = 0.0
        profitper = 0.0
        try:
            profitval = mktval - totalcost
            profitper = profitval / totalcost
        except ZeroDivisionError:
            profitval = "N/A"
            profitper = "N/A"

        self.totalcost.setText(QString(str(totalcost)))
        self.mktval.setText(QString(str(mktval)))
        self.profitval.setText(QString(str(profitval)))
        self.profitper.setText(QString(str(profitper)))

    @pyqtSlot()
    def on_ok_clicked(self):
        self.done(0)

    def setup(self):
        self.setupUi(self)

