# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tradeui.ui'
#
# Created: Sun May 23 17:01:26 2010
#      by: PyQt4 UI code generator 4.7.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1076, 615)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_6 = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout_6.setObjectName("gridLayout_6")
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
        self.pricepolicybuy.setMaximumSize(QtCore.QSize(60, 16777215))
        self.pricepolicybuy.setObjectName("pricepolicybuy")
        self.gridLayout_2.addWidget(self.pricepolicybuy, 0, 1, 1, 1)
        self.label_4 = QtGui.QLabel(self.groupBox_2)
        self.label_4.setObjectName("label_4")
        self.gridLayout_2.addWidget(self.label_4, 0, 2, 1, 1)
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
        self.buypricefixspin = QtGui.QDoubleSpinBox(self.groupBox_2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buypricefixspin.sizePolicy().hasHeightForWidth())
        self.buypricefixspin.setSizePolicy(sizePolicy)
        self.buypricefixspin.setFrame(True)
        self.buypricefixspin.setButtonSymbols(QtGui.QAbstractSpinBox.UpDownArrows)
        self.buypricefixspin.setMinimum(-999.99)
        self.buypricefixspin.setMaximum(999.99)
        self.buypricefixspin.setSingleStep(0.01)
        self.buypricefixspin.setObjectName("buypricefixspin")
        self.gridLayout_2.addWidget(self.buypricefixspin, 0, 3, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox_2, 0, 0, 1, 1)
        self.groupBox_5 = QtGui.QGroupBox(self.tab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_5.sizePolicy().hasHeightForWidth())
        self.groupBox_5.setSizePolicy(sizePolicy)
        self.groupBox_5.setObjectName("groupBox_5")
        self.gridLayout_7 = QtGui.QGridLayout(self.groupBox_5)
        self.gridLayout_7.setObjectName("gridLayout_7")
        self.opensifbtn = QtGui.QPushButton(self.groupBox_5)
        self.opensifbtn.setObjectName("opensifbtn")
        self.gridLayout_7.addWidget(self.opensifbtn, 0, 4, 1, 1)
        self.cancelopensifbtn = QtGui.QPushButton(self.groupBox_5)
        self.cancelopensifbtn.setObjectName("cancelopensifbtn")
        self.gridLayout_7.addWidget(self.cancelopensifbtn, 0, 5, 1, 1)
        self.label_9 = QtGui.QLabel(self.groupBox_5)
        self.label_9.setObjectName("label_9")
        self.gridLayout_7.addWidget(self.label_9, 0, 2, 1, 1)
        self.openpricecmbox = QtGui.QComboBox(self.groupBox_5)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.openpricecmbox.sizePolicy().hasHeightForWidth())
        self.openpricecmbox.setSizePolicy(sizePolicy)
        self.openpricecmbox.setMaximumSize(QtCore.QSize(60, 16777215))
        self.openpricecmbox.setObjectName("openpricecmbox")
        self.gridLayout_7.addWidget(self.openpricecmbox, 0, 1, 1, 1)
        self.label_8 = QtGui.QLabel(self.groupBox_5)
        self.label_8.setObjectName("label_8")
        self.gridLayout_7.addWidget(self.label_8, 0, 0, 1, 1)
        self.openpricefixspin = QtGui.QDoubleSpinBox(self.groupBox_5)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.openpricefixspin.sizePolicy().hasHeightForWidth())
        self.openpricefixspin.setSizePolicy(sizePolicy)
        self.openpricefixspin.setFrame(True)
        self.openpricefixspin.setButtonSymbols(QtGui.QAbstractSpinBox.UpDownArrows)
        self.openpricefixspin.setDecimals(1)
        self.openpricefixspin.setMinimum(-10000.0)
        self.openpricefixspin.setMaximum(10000.0)
        self.openpricefixspin.setSingleStep(0.2)
        self.openpricefixspin.setObjectName("openpricefixspin")
        self.gridLayout_7.addWidget(self.openpricefixspin, 0, 3, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox_5, 0, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_3.addItem(spacerItem, 0, 2, 1, 1)
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
        self.pricepolicysell.setMaximumSize(QtCore.QSize(60, 16777215))
        self.pricepolicysell.setObjectName("pricepolicysell")
        self.gridLayout.addWidget(self.pricepolicysell, 0, 1, 1, 1)
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 2, 1, 1)
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
        self.sellpricefixspin = QtGui.QDoubleSpinBox(self.groupBox)
        self.sellpricefixspin.setMinimum(-999.99)
        self.sellpricefixspin.setMaximum(999.99)
        self.sellpricefixspin.setSingleStep(0.01)
        self.sellpricefixspin.setObjectName("sellpricefixspin")
        self.gridLayout.addWidget(self.sellpricefixspin, 0, 3, 1, 1)
        self.gridLayout_4.addWidget(self.groupBox, 0, 0, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_4.addItem(spacerItem1, 0, 2, 1, 1)
        self.groupBox_4 = QtGui.QGroupBox(self.tab_2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_4.sizePolicy().hasHeightForWidth())
        self.groupBox_4.setSizePolicy(sizePolicy)
        self.groupBox_4.setObjectName("groupBox_4")
        self.gridLayout_8 = QtGui.QGridLayout(self.groupBox_4)
        self.gridLayout_8.setObjectName("gridLayout_8")
        self.closesifbtn = QtGui.QPushButton(self.groupBox_4)
        self.closesifbtn.setObjectName("closesifbtn")
        self.gridLayout_8.addWidget(self.closesifbtn, 0, 5, 1, 1)
        self.cancelclosesifbtn = QtGui.QPushButton(self.groupBox_4)
        self.cancelclosesifbtn.setObjectName("cancelclosesifbtn")
        self.gridLayout_8.addWidget(self.cancelclosesifbtn, 0, 6, 1, 1)
        self.closepricecmbox = QtGui.QComboBox(self.groupBox_4)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.closepricecmbox.sizePolicy().hasHeightForWidth())
        self.closepricecmbox.setSizePolicy(sizePolicy)
        self.closepricecmbox.setMaximumSize(QtCore.QSize(60, 16777215))
        self.closepricecmbox.setObjectName("closepricecmbox")
        self.gridLayout_8.addWidget(self.closepricecmbox, 0, 2, 1, 1)
        self.label_10 = QtGui.QLabel(self.groupBox_4)
        self.label_10.setObjectName("label_10")
        self.gridLayout_8.addWidget(self.label_10, 0, 1, 1, 1)
        self.label_11 = QtGui.QLabel(self.groupBox_4)
        self.label_11.setObjectName("label_11")
        self.gridLayout_8.addWidget(self.label_11, 0, 3, 1, 1)
        self.closepricefixspin = QtGui.QDoubleSpinBox(self.groupBox_4)
        self.closepricefixspin.setDecimals(1)
        self.closepricefixspin.setMinimum(-10000.0)
        self.closepricefixspin.setMaximum(10000.0)
        self.closepricefixspin.setSingleStep(0.2)
        self.closepricefixspin.setObjectName("closepricefixspin")
        self.gridLayout_8.addWidget(self.closepricefixspin, 0, 4, 1, 1)
        self.gridLayout_4.addWidget(self.groupBox_4, 0, 1, 1, 1)
        self.tabWidget.addTab(self.tab_2, "")
        self.gridLayout_6.addWidget(self.tabWidget, 0, 0, 1, 1)
        self.groupBox_3 = QtGui.QGroupBox(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_3.sizePolicy().hasHeightForWidth())
        self.groupBox_3.setSizePolicy(sizePolicy)
        self.groupBox_3.setTitle("")
        self.groupBox_3.setObjectName("groupBox_3")
        self.gridLayout_5 = QtGui.QGridLayout(self.groupBox_3)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.label_5 = QtGui.QLabel(self.groupBox_3)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy)
        self.label_5.setObjectName("label_5")
        self.gridLayout_5.addWidget(self.label_5, 0, 0, 1, 1)
        self.hs300line = QtGui.QLineEdit(self.groupBox_3)
        self.hs300line.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.hs300line.sizePolicy().hasHeightForWidth())
        self.hs300line.setSizePolicy(sizePolicy)
        self.hs300line.setMinimumSize(QtCore.QSize(0, 0))
        self.hs300line.setMaximumSize(QtCore.QSize(60, 16777215))
        self.hs300line.setReadOnly(True)
        self.hs300line.setObjectName("hs300line")
        self.gridLayout_5.addWidget(self.hs300line, 0, 1, 1, 1)
        self.label_6 = QtGui.QLabel(self.groupBox_3)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy)
        self.label_6.setObjectName("label_6")
        self.gridLayout_5.addWidget(self.label_6, 0, 2, 1, 1)
        self.sindexcmbox = QtGui.QComboBox(self.groupBox_3)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sindexcmbox.sizePolicy().hasHeightForWidth())
        self.sindexcmbox.setSizePolicy(sizePolicy)
        self.sindexcmbox.setObjectName("sindexcmbox")
        self.gridLayout_5.addWidget(self.sindexcmbox, 0, 3, 1, 1)
        self.sindexline = QtGui.QLineEdit(self.groupBox_3)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sindexline.sizePolicy().hasHeightForWidth())
        self.sindexline.setSizePolicy(sizePolicy)
        self.sindexline.setMinimumSize(QtCore.QSize(0, 0))
        self.sindexline.setMaximumSize(QtCore.QSize(60, 16777215))
        self.sindexline.setReadOnly(True)
        self.sindexline.setObjectName("sindexline")
        self.gridLayout_5.addWidget(self.sindexline, 0, 4, 1, 1)
        self.label_7 = QtGui.QLabel(self.groupBox_3)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_7.sizePolicy().hasHeightForWidth())
        self.label_7.setSizePolicy(sizePolicy)
        self.label_7.setObjectName("label_7")
        self.gridLayout_5.addWidget(self.label_7, 0, 5, 1, 1)
        self.basediffline = QtGui.QLineEdit(self.groupBox_3)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.basediffline.sizePolicy().hasHeightForWidth())
        self.basediffline.setSizePolicy(sizePolicy)
        self.basediffline.setMinimumSize(QtCore.QSize(0, 0))
        self.basediffline.setMaximumSize(QtCore.QSize(60, 16777215))
        self.basediffline.setReadOnly(True)
        self.basediffline.setObjectName("basediffline")
        self.gridLayout_5.addWidget(self.basediffline, 0, 6, 1, 1)
        spacerItem2 = QtGui.QSpacerItem(383, 0, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_5.addItem(spacerItem2, 0, 7, 1, 1)
        self.gridLayout_6.addWidget(self.groupBox_3, 2, 0, 1, 1)
        self.stock = QtGui.QTableView(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.stock.sizePolicy().hasHeightForWidth())
        self.stock.setSizePolicy(sizePolicy)
        self.stock.setObjectName("stock")
        self.gridLayout_6.addWidget(self.stock, 4, 0, 1, 1)
        self.stockindex = QtGui.QTableView(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.stockindex.sizePolicy().hasHeightForWidth())
        self.stockindex.setSizePolicy(sizePolicy)
        self.stockindex.setMaximumSize(QtCore.QSize(16777215, 50))
        self.stockindex.setObjectName("stockindex")
        self.gridLayout_6.addWidget(self.stockindex, 1, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setEnabled(True)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1076, 18))
        self.menubar.setNativeMenuBar(True)
        self.menubar.setObjectName("menubar")
        self.menu = QtGui.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.stockinfoact = QtGui.QAction(MainWindow)
        self.stockinfoact.setObjectName("stockinfoact")
        self.posstatact = QtGui.QAction(MainWindow)
        self.posstatact.setObjectName("posstatact")
        self.menu.addAction(self.stockinfoact)
        self.menu.addAction(self.posstatact)
        self.menubar.addAction(self.menu.menuAction())

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "EasyTrader $Id$", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_2.setTitle(QtGui.QApplication.translate("MainWindow", "股票组合", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("MainWindow", "买入价格", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("MainWindow", "修正", None, QtGui.QApplication.UnicodeUTF8))
        self.buyorder.setText(QtGui.QApplication.translate("MainWindow", "买入/补买", None, QtGui.QApplication.UnicodeUTF8))
        self.cancelbuyorder.setText(QtGui.QApplication.translate("MainWindow", "撤买", None, QtGui.QApplication.UnicodeUTF8))
        self.autosubmit_2.setText(QtGui.QApplication.translate("MainWindow", "自动下单", None, QtGui.QApplication.UnicodeUTF8))
        self.saveorder_2.setText(QtGui.QApplication.translate("MainWindow", "保存组合", None, QtGui.QApplication.UnicodeUTF8))
        self.buypricefixspin.setPrefix(QtGui.QApplication.translate("MainWindow", "￥", None, QtGui.QApplication.UnicodeUTF8))
        self.buypricefixspin.setSuffix(QtGui.QApplication.translate("MainWindow", "元", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_5.setTitle(QtGui.QApplication.translate("MainWindow", "股指期货", None, QtGui.QApplication.UnicodeUTF8))
        self.opensifbtn.setText(QtGui.QApplication.translate("MainWindow", "空开", None, QtGui.QApplication.UnicodeUTF8))
        self.cancelopensifbtn.setText(QtGui.QApplication.translate("MainWindow", "撤单", None, QtGui.QApplication.UnicodeUTF8))
        self.label_9.setText(QtGui.QApplication.translate("MainWindow", "修正", None, QtGui.QApplication.UnicodeUTF8))
        self.label_8.setText(QtGui.QApplication.translate("MainWindow", "开仓价格", None, QtGui.QApplication.UnicodeUTF8))
        self.openpricefixspin.setPrefix(QtGui.QApplication.translate("MainWindow", "￥", None, QtGui.QApplication.UnicodeUTF8))
        self.openpricefixspin.setSuffix(QtGui.QApplication.translate("MainWindow", "元", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QtGui.QApplication.translate("MainWindow", "建仓", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("MainWindow", "股票组合", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("MainWindow", "卖出价格", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("MainWindow", "修正", None, QtGui.QApplication.UnicodeUTF8))
        self.sellorder.setText(QtGui.QApplication.translate("MainWindow", "卖出/补卖", None, QtGui.QApplication.UnicodeUTF8))
        self.cancelsellorder.setText(QtGui.QApplication.translate("MainWindow", "撤卖", None, QtGui.QApplication.UnicodeUTF8))
        self.autosubmit.setText(QtGui.QApplication.translate("MainWindow", "自动下单", None, QtGui.QApplication.UnicodeUTF8))
        self.saveorder.setText(QtGui.QApplication.translate("MainWindow", "保存组合", None, QtGui.QApplication.UnicodeUTF8))
        self.sellpricefixspin.setPrefix(QtGui.QApplication.translate("MainWindow", "￥", None, QtGui.QApplication.UnicodeUTF8))
        self.sellpricefixspin.setSuffix(QtGui.QApplication.translate("MainWindow", "元", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_4.setTitle(QtGui.QApplication.translate("MainWindow", "股指期货", None, QtGui.QApplication.UnicodeUTF8))
        self.closesifbtn.setText(QtGui.QApplication.translate("MainWindow", "空平", None, QtGui.QApplication.UnicodeUTF8))
        self.cancelclosesifbtn.setText(QtGui.QApplication.translate("MainWindow", "撤单", None, QtGui.QApplication.UnicodeUTF8))
        self.label_10.setText(QtGui.QApplication.translate("MainWindow", "平仓价格", None, QtGui.QApplication.UnicodeUTF8))
        self.label_11.setText(QtGui.QApplication.translate("MainWindow", "修正", None, QtGui.QApplication.UnicodeUTF8))
        self.closepricefixspin.setPrefix(QtGui.QApplication.translate("MainWindow", "￥", None, QtGui.QApplication.UnicodeUTF8))
        self.closepricefixspin.setSuffix(QtGui.QApplication.translate("MainWindow", "元", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QtGui.QApplication.translate("MainWindow", "平仓", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("MainWindow", "沪深300：", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("MainWindow", "股指期货：", None, QtGui.QApplication.UnicodeUTF8))
        self.label_7.setText(QtGui.QApplication.translate("MainWindow", "基差：", None, QtGui.QApplication.UnicodeUTF8))
        self.menu.setTitle(QtGui.QApplication.translate("MainWindow", "查看", None, QtGui.QApplication.UnicodeUTF8))
        self.stockinfoact.setText(QtGui.QApplication.translate("MainWindow", "股份查询", None, QtGui.QApplication.UnicodeUTF8))
        self.posstatact.setText(QtGui.QApplication.translate("MainWindow", "持仓统计", None, QtGui.QApplication.UnicodeUTF8))

