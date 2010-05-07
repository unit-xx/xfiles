# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'stockqueryui.ui'
#
# Created: Fri May 07 11:19:05 2010
#      by: PyQt4 UI code generator 4.7.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_stockquery(object):
    def setupUi(self, stockquery):
        stockquery.setObjectName("stockquery")
        stockquery.resize(757, 486)
        stockquery.setSizeGripEnabled(False)
        self.gridLayout = QtGui.QGridLayout(stockquery)
        self.gridLayout.setObjectName("gridLayout")
        self.groupBox = QtGui.QGroupBox(stockquery)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setTitle("")
        self.groupBox.setObjectName("groupBox")
        self.formLayout = QtGui.QFormLayout(self.groupBox)
        self.formLayout.setObjectName("formLayout")
        self.refresh = QtGui.QPushButton(self.groupBox)
        self.refresh.setObjectName("refresh")
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.refresh)
        self.quit = QtGui.QPushButton(self.groupBox)
        self.quit.setObjectName("quit")
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.quit)
        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(554, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 0, 1, 1, 1)
        self.stockinfo = QtGui.QTableView(stockquery)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.stockinfo.sizePolicy().hasHeightForWidth())
        self.stockinfo.setSizePolicy(sizePolicy)
        self.stockinfo.setObjectName("stockinfo")
        self.gridLayout.addWidget(self.stockinfo, 1, 0, 1, 2)

        self.retranslateUi(stockquery)
        QtCore.QMetaObject.connectSlotsByName(stockquery)

    def retranslateUi(self, stockquery):
        stockquery.setWindowTitle(QtGui.QApplication.translate("stockquery", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.refresh.setText(QtGui.QApplication.translate("stockquery", "刷新", None, QtGui.QApplication.UnicodeUTF8))
        self.quit.setText(QtGui.QApplication.translate("stockquery", "退出", None, QtGui.QApplication.UnicodeUTF8))

