# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tradeui.ui'
#
# Created: Thu Apr 22 16:24:26 2010
#      by: PyQt4 UI code generator 4.7.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(876, 642)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("zjzq.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_2 = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.groupBox = QtGui.QGroupBox(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setTitle("")
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtGui.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtGui.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.pricepolicylist = QtGui.QComboBox(self.groupBox)
        self.pricepolicylist.setObjectName("pricepolicylist")
        self.gridLayout.addWidget(self.pricepolicylist, 0, 1, 1, 1)
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 2, 1, 1)
        self.pricefix = QtGui.QLineEdit(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pricefix.sizePolicy().hasHeightForWidth())
        self.pricefix.setSizePolicy(sizePolicy)
        self.pricefix.setObjectName("pricefix")
        self.gridLayout.addWidget(self.pricefix, 0, 3, 1, 1)
        self.submitorder = QtGui.QPushButton(self.groupBox)
        self.submitorder.setObjectName("submitorder")
        self.gridLayout.addWidget(self.submitorder, 0, 4, 1, 1)
        self.cancelorder = QtGui.QPushButton(self.groupBox)
        self.cancelorder.setObjectName("cancelorder")
        self.gridLayout.addWidget(self.cancelorder, 0, 5, 1, 1)
        self.autosubmit = QtGui.QPushButton(self.groupBox)
        self.autosubmit.setObjectName("autosubmit")
        self.gridLayout.addWidget(self.autosubmit, 0, 7, 1, 1)
        self.genbackuporder = QtGui.QPushButton(self.groupBox)
        self.genbackuporder.setObjectName("genbackuporder")
        self.gridLayout.addWidget(self.genbackuporder, 0, 6, 1, 1)
        self.saveorder = QtGui.QPushButton(self.groupBox)
        self.saveorder.setObjectName("saveorder")
        self.gridLayout.addWidget(self.saveorder, 0, 8, 1, 1)
        self.gridLayout_2.addWidget(self.groupBox, 0, 0, 1, 1)
        self.tabWidget = QtGui.QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtGui.QWidget()
        self.tab.setObjectName("tab")
        self.horizontalLayout = QtGui.QHBoxLayout(self.tab)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.stock = QtGui.QTableView(self.tab)
        self.stock.setObjectName("stock")
        self.horizontalLayout.addWidget(self.stock)
        self.tabWidget.addTab(self.tab, "")
        self.gridLayout_2.addWidget(self.tabWidget, 1, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setEnabled(True)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 876, 19))
        self.menubar.setNativeMenuBar(True)
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "EasyTrader", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("MainWindow", "报价策略", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("MainWindow", "修正", None, QtGui.QApplication.UnicodeUTF8))
        self.submitorder.setText(QtGui.QApplication.translate("MainWindow", "下单/补单", None, QtGui.QApplication.UnicodeUTF8))
        self.cancelorder.setText(QtGui.QApplication.translate("MainWindow", "取消委托", None, QtGui.QApplication.UnicodeUTF8))
        self.autosubmit.setText(QtGui.QApplication.translate("MainWindow", "自动下单", None, QtGui.QApplication.UnicodeUTF8))
        self.genbackuporder.setText(QtGui.QApplication.translate("MainWindow", "生成补单", None, QtGui.QApplication.UnicodeUTF8))
        self.saveorder.setText(QtGui.QApplication.translate("MainWindow", "保存组合", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QtGui.QApplication.translate("MainWindow", "投资组合", None, QtGui.QApplication.UnicodeUTF8))
