# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'crabmonui.ui'
#
# Created: Fri Jan 10 13:25:01 2014
#      by: PyQt4 UI code generator 4.10.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_crabmainwin(object):
    def setupUi(self, crabmainwin):
        crabmainwin.setObjectName(_fromUtf8("crabmainwin"))
        crabmainwin.resize(659, 600)
        self.centralwidget = QtGui.QWidget(crabmainwin)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label = QtGui.QLabel(self.centralwidget)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.stratcmbo = QtGui.QComboBox(self.centralwidget)
        self.stratcmbo.setObjectName(_fromUtf8("stratcmbo"))
        self.gridLayout.addWidget(self.stratcmbo, 0, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(533, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 0, 4, 1, 1)
        self.positiontbl = QtGui.QTableView(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.positiontbl.sizePolicy().hasHeightForWidth())
        self.positiontbl.setSizePolicy(sizePolicy)
        self.positiontbl.setObjectName(_fromUtf8("positiontbl"))
        self.gridLayout.addWidget(self.positiontbl, 1, 0, 1, 5)
        self.ordertbl = QtGui.QTableView(self.centralwidget)
        self.ordertbl.setObjectName(_fromUtf8("ordertbl"))
        self.gridLayout.addWidget(self.ordertbl, 2, 0, 1, 5)
        self.label_2 = QtGui.QLabel(self.centralwidget)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 0, 2, 1, 1)
        self.tbnameline = QtGui.QLineEdit(self.centralwidget)
        self.tbnameline.setMinimumSize(QtCore.QSize(100, 0))
        self.tbnameline.setText(_fromUtf8(""))
        self.tbnameline.setReadOnly(True)
        self.tbnameline.setObjectName(_fromUtf8("tbnameline"))
        self.gridLayout.addWidget(self.tbnameline, 0, 3, 1, 1)
        crabmainwin.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(crabmainwin)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 659, 23))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        crabmainwin.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(crabmainwin)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        crabmainwin.setStatusBar(self.statusbar)

        self.retranslateUi(crabmainwin)
        QtCore.QMetaObject.connectSlotsByName(crabmainwin)

    def retranslateUi(self, crabmainwin):
        crabmainwin.setWindowTitle(_translate("crabmainwin", "跨期套利监控", None))
        self.label.setText(_translate("crabmainwin", "策略", None))
        self.label_2.setText(_translate("crabmainwin", "账目", None))

# $Id$ 
