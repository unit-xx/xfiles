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
        totalcost = 0.0
        mktval = 0.0
        stopmktval = 0.0
        for scode in self.portfolio.stockinfo:
            si = self.portfolio.stockinfo[scode]
            totalcost = totalcost + si["currentbuycost"]
            if si["latestprice"] == 0.0:
                mktval = mktval + si["currentbuycount"] * si["close"]
            else:
                mktval = mktval + si["currentbuycount"] * si["latestprice"]
            try:
                if si["stopped"]:
                    if si["latestprice"] == 0.0:
                        stopmktval = stopmktval + si["currentbuycount"] * si["close"]
                    else:
                        stopmktval = stopmktval + si["currentbuycount"] * si["latestprice"]
            except KeyError:
                pass

        profitval = 0.0
        profitper = 0.0
        profitval2 = 0.0
        profitper2 = 0.0
        try:
            profitval = mktval - totalcost
            profitval2 = profitval - stopmktval
            profitper = profitval / totalcost * 100
            profitper2 = profitval2 / totalcost * 100
        except ZeroDivisionError:
            pass

        wan = 10000.0
        self.totalcost.setText(QString(u"%0.2f万" % (totalcost/wan)))
        self.mktval.setText(QString(u"%0.2f万 (%0.2f万)" % (mktval/wan, (mktval-stopmktval)/wan)))
        self.profitval.setText(QString(u"%0.2f万 (%0.2f万)" % (profitval/wan, profitval2/wan)))
        self.profitper.setText(QString(u"%0.2f%% (%0.2f%%)" % (profitper, profitper2)))

        sigainp = self.portfolio.sindexinfo["earning"]
        sigainv = sigainp * 300.0
        self.sigain.setText(QString(u"%d 点 = %0.2f万" % (sigainp, sigainv/wan)))

        totalgain = sigainv + profitval
        totalgain2 = sigainv + profitval2
        self.totalgain.setText(QString(u"%0.2f万 (%0.2f万)" % (totalgain/wan, totalgain2/wan)))


    @pyqtSlot()
    def on_ok_clicked(self):
        self.done(0)

    def setup(self):
        self.setupUi(self)

