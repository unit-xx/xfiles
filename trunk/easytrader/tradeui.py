# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tradeui.ui'
#
# Created: Thu May 06 16:36:24 2010
#      by: PyQt4 UI code generator 4.7.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(880, 605)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtGui.QTabWidget(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtGui.QWidget()
        self.tab.setObjectName("tab")
        self.gridLayout_3 = QtGui.QGridLayout(self.tab)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.groupBox_2 = QtGui.QGroupBox(self.tab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_2.sizePolicy().hasHeightForWidth())
        self.groupBox_2.setSizePolicy(sizePolicy)
        self.groupBox_2.setTitle("")
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_2 = QtGui.QGridLayout(self.groupBox_2)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label_3 = QtGui.QLabel(self.groupBox_2)
        self.label_3.setObjectName("label_3")
        self.gridLayout_2.addWidget(self.label_3, 0, 0, 1, 1)
        self.pricepolicybuy = QtGui.QComboBox(self.groupBox_2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pricepolicybuy.sizePolicy().hasHeightForWidth())
        self.pricepolicybuy.setSizePolicy(sizePolicy)
        self.pricepolicybuy.setObjectName("pricepolicybuy")
        self.gridLayout_2.addWidget(self.pricepolicybuy, 0, 1, 1, 1)
        self.label_4 = QtGui.QLabel(self.groupBox_2)
        self.label_4.setObjectName("label_4")
        self.gridLayout_2.addWidget(self.label_4, 0, 2, 1, 1)
        self.pricefixbuy = QtGui.QLineEdit(self.groupBox_2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pricefixbuy.sizePolicy().hasHeightForWidth())
        self.pricefixbuy.setSizePolicy(sizePolicy)
        self.pricefixbuy.setObjectName("pricefixbuy")
        self.gridLayout_2.addWidget(self.pricefixbuy, 0, 3, 1, 1)
        self.buyorder = QtGui.QPushButton(self.groupBox_2)
        self.buyorder.setObjectName("buyorder")
        self.gridLayout_2.addWidget(self.buyorder, 0, 4, 1, 1)
        self.cancelbuyorder = QtGui.QPushButton(self.groupBox_2)
        self.cancelbuyorder.setObjectName("cancelbuyorder")
        self.gridLayout_2.addWidget(self.cancelbuyorder, 0, 5, 1, 1)
        self.autosubmit_2 = QtGui.QPushButton(self.groupBox_2)
        self.autosubmit_2.setObjectName("autosubmit_2")
        self.gridLayout_2.addWidget(self.autosubmit_2, 0, 6, 1, 1)
        self.saveorder_2 = QtGui.QPushButton(self.groupBox_2)
        self.saveorder_2.setObjectName("saveorder_2")
        self.gridLayout_2.addWidget(self.saveorder_2, 0, 7, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox_2, 0, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_3.addItem(spacerItem, 0, 1, 1, 1)
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.gridLayout_4 = QtGui.QGridLayout(self.tab_2)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.groupBox = QtGui.QGroupBox(self.tab_2)
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
        self.pricepolicysell = QtGui.QComboBox(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pricepolicysell.sizePolicy().hasHeightForWidth())
        self.pricepolicysell.setSizePolicy(sizePolicy)
        self.pricepolicysell.setObjectName("pricepolicysell")
        self.gridLayout.addWidget(self.pricepolicysell, 0, 1, 1, 1)
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 2, 1, 1)
        self.pricefixsell = QtGui.QLineEdit(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pricefixsell.sizePolicy().hasHeightForWidth())
        self.pricefixsell.setSizePolicy(sizePolicy)
        self.pricefixsell.setObjectName("pricefixsell")
        self.gridLayout.addWidget(self.pricefixsell, 0, 3, 1, 1)
        self.sellorder = QtGui.QPushButton(self.groupBox)
        self.sellorder.setObjectName("sellorder")
        self.gridLayout.addWidget(self.sellorder, 0, 4, 1, 1)
        self.cancelsellorder = QtGui.QPushButton(self.groupBox)
        self.cancelsellorder.setObjectName("cancelsellorder")
        self.gridLayout.addWidget(self.cancelsellorder, 0, 5, 1, 1)
        self.autosubmit = QtGui.QPushButton(self.groupBox)
        self.autosubmit.setObjectName("autosubmit")
        self.gridLayout.addWidget(self.autosubmit, 0, 6, 1, 1)
        self.saveorder = QtGui.QPushButton(self.groupBox)
        self.saveorder.setObjectName("saveorder")
        self.gridLayout.addWidget(self.saveorder, 0, 7, 1, 1)
        self.gridLayout_4.addWidget(self.groupBox, 0, 0, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_4.addItem(spacerItem1, 0, 1, 1, 1)
        self.tabWidget.addTab(self.tab_2, "")
        self.verticalLayout.addWidget(self.tabWidget)
        self.stock = QtGui.QTableView(self.centralwidget)
        self.stock.setObjectName("stock")
        self.verticalLayout.addWidget(self.stock)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setEnabled(True)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 880, 19))
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
        self.label_3.setText(QtGui.QApplication.translate("MainWindow", "买入价格", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("MainWindow", "修正", None, QtGui.QApplication.UnicodeUTF8))
        self.buyorder.setText(QtGui.QApplication.translate("MainWindow", "买入/补买", None, QtGui.QApplication.UnicodeUTF8))
        self.cancelbuyorder.setText(QtGui.QApplication.translate("MainWindow", "撤买", None, QtGui.QApplication.UnicodeUTF8))
        self.autosubmit_2.setText(QtGui.QApplication.translate("MainWindow", "自动下单", None, QtGui.QApplication.UnicodeUTF8))
        self.saveorder_2.setText(QtGui.QApplication.translate("MainWindow", "保存组合", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QtGui.QApplication.translate("MainWindow", "建仓", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("MainWindow", "卖出价格", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("MainWindow", "修正", None, QtGui.QApplication.UnicodeUTF8))
        self.sellorder.setText(QtGui.QApplication.translate("MainWindow", "卖出/补卖", None, QtGui.QApplication.UnicodeUTF8))
        self.cancelsellorder.setText(QtGui.QApplication.translate("MainWindow", "撤卖", None, QtGui.QApplication.UnicodeUTF8))
        self.autosubmit.setText(QtGui.QApplication.translate("MainWindow", "自动下单", None, QtGui.QApplication.UnicodeUTF8))
        self.saveorder.setText(QtGui.QApplication.translate("MainWindow", "保存组合", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QtGui.QApplication.translate("MainWindow", "平仓", None, QtGui.QApplication.UnicodeUTF8))

