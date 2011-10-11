# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'stockqueryui.ui'
#
# Created: Mon Oct 10 13:46:58 2011
#      by: PyQt4 UI code generator 4.8.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_stockquery(object):
    def setupUi(self, stockquery):
        stockquery.setObjectName(_fromUtf8("stockquery"))
        stockquery.resize(977, 486)
        stockquery.setSizeGripEnabled(False)
        self.gridLayout_4 = QtGui.QGridLayout(stockquery)
        self.gridLayout_4.setObjectName(_fromUtf8("gridLayout_4"))
        self.groupBox = QtGui.QGroupBox(stockquery)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setTitle(_fromUtf8(""))
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.gridLayout = QtGui.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.refresh = QtGui.QPushButton(self.groupBox)
        self.refresh.setObjectName(_fromUtf8("refresh"))
        self.gridLayout.addWidget(self.refresh, 0, 0, 1, 1)
        self.exportsellbtn = QtGui.QPushButton(self.groupBox)
        self.exportsellbtn.setObjectName(_fromUtf8("exportsellbtn"))
        self.gridLayout.addWidget(self.exportsellbtn, 0, 1, 1, 1)
        self.sifcodeline = QtGui.QLineEdit(self.groupBox)
        self.sifcodeline.setObjectName(_fromUtf8("sifcodeline"))
        self.gridLayout.addWidget(self.sifcodeline, 0, 3, 1, 1)
        self.sifshareline = QtGui.QLineEdit(self.groupBox)
        self.sifshareline.setObjectName(_fromUtf8("sifshareline"))
        self.gridLayout.addWidget(self.sifshareline, 0, 5, 1, 1)
        self.label = QtGui.QLabel(self.groupBox)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 2, 1, 1)
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 0, 4, 1, 1)
        self.quit = QtGui.QPushButton(self.groupBox)
        self.quit.setObjectName(_fromUtf8("quit"))
        self.gridLayout.addWidget(self.quit, 0, 6, 1, 1)
        self.gridLayout_4.addWidget(self.groupBox, 0, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(554, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_4.addItem(spacerItem, 0, 1, 1, 1)
        self.tabWidget = QtGui.QTabWidget(stockquery)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.tab = QtGui.QWidget()
        self.tab.setObjectName(_fromUtf8("tab"))
        self.gridLayout_2 = QtGui.QGridLayout(self.tab)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.stockinfo = QtGui.QTableView(self.tab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.stockinfo.sizePolicy().hasHeightForWidth())
        self.stockinfo.setSizePolicy(sizePolicy)
        self.stockinfo.setObjectName(_fromUtf8("stockinfo"))
        self.gridLayout_2.addWidget(self.stockinfo, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab, _fromUtf8(""))
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName(_fromUtf8("tab_2"))
        self.gridLayout_3 = QtGui.QGridLayout(self.tab_2)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.accinfotext = QtGui.QTextEdit(self.tab_2)
        self.accinfotext.setObjectName(_fromUtf8("accinfotext"))
        self.gridLayout_3.addWidget(self.accinfotext, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab_2, _fromUtf8(""))
        self.gridLayout_4.addWidget(self.tabWidget, 1, 0, 1, 2)

        self.retranslateUi(stockquery)
        self.tabWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(stockquery)
        stockquery.setTabOrder(self.refresh, self.stockinfo)

    def retranslateUi(self, stockquery):
        stockquery.setWindowTitle(QtGui.QApplication.translate("stockquery", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.refresh.setText(QtGui.QApplication.translate("stockquery", "刷新", None, QtGui.QApplication.UnicodeUTF8))
        self.exportsellbtn.setText(QtGui.QApplication.translate("stockquery", "导出卖单", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("stockquery", "期货代码", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("stockquery", "期货手数", None, QtGui.QApplication.UnicodeUTF8))
        self.quit.setText(QtGui.QApplication.translate("stockquery", "退出", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QtGui.QApplication.translate("stockquery", "持股", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QtGui.QApplication.translate("stockquery", "账户", None, QtGui.QApplication.UnicodeUTF8))

