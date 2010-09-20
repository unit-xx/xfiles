# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'stockqueryui.ui'
#
# Created: Mon Sep 20 09:32:29 2010
#      by: PyQt4 UI code generator 4.7.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_stockquery(object):
    def setupUi(self, stockquery):
        stockquery.setObjectName("stockquery")
        stockquery.resize(977, 486)
        stockquery.setSizeGripEnabled(False)
        self.gridLayout_2 = QtGui.QGridLayout(stockquery)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.groupBox = QtGui.QGroupBox(stockquery)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setTitle("")
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtGui.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.refresh = QtGui.QPushButton(self.groupBox)
        self.refresh.setObjectName("refresh")
        self.gridLayout.addWidget(self.refresh, 0, 0, 1, 1)
        self.exportsellbtn = QtGui.QPushButton(self.groupBox)
        self.exportsellbtn.setObjectName("exportsellbtn")
        self.gridLayout.addWidget(self.exportsellbtn, 0, 1, 1, 1)
        self.quit = QtGui.QPushButton(self.groupBox)
        self.quit.setObjectName("quit")
        self.gridLayout.addWidget(self.quit, 0, 2, 1, 1)
        self.gridLayout_2.addWidget(self.groupBox, 0, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(554, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem, 0, 1, 1, 1)
        self.stockinfo = QtGui.QTableView(stockquery)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.stockinfo.sizePolicy().hasHeightForWidth())
        self.stockinfo.setSizePolicy(sizePolicy)
        self.stockinfo.setObjectName("stockinfo")
        self.gridLayout_2.addWidget(self.stockinfo, 1, 0, 1, 2)

        self.retranslateUi(stockquery)
        QtCore.QMetaObject.connectSlotsByName(stockquery)
        stockquery.setTabOrder(self.refresh, self.quit)
        stockquery.setTabOrder(self.quit, self.stockinfo)

    def retranslateUi(self, stockquery):
        stockquery.setWindowTitle(QtGui.QApplication.translate("stockquery", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.refresh.setText(QtGui.QApplication.translate("stockquery", "刷新", None, QtGui.QApplication.UnicodeUTF8))
        self.exportsellbtn.setText(QtGui.QApplication.translate("stockquery", "导出卖单", None, QtGui.QApplication.UnicodeUTF8))
        self.quit.setText(QtGui.QApplication.translate("stockquery", "退出", None, QtGui.QApplication.UnicodeUTF8))

