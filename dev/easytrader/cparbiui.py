# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'cparbiui.ui'
#
# Created: Wed Jul 28 14:13:31 2010
#      by: PyQt4 UI code generator 4.7.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(458, 244)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_3 = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.groupBox = QtGui.QGroupBox(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtGui.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.arbitbl = QtGui.QTableView(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.arbitbl.sizePolicy().hasHeightForWidth())
        self.arbitbl.setSizePolicy(sizePolicy)
        self.arbitbl.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.arbitbl.setObjectName("arbitbl")
        self.gridLayout.addWidget(self.arbitbl, 0, 0, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox, 0, 0, 1, 7)
        self.label_3 = QtGui.QLabel(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)
        self.label_3.setObjectName("label_3")
        self.gridLayout_3.addWidget(self.label_3, 1, 0, 1, 1)
        self.openbasediffline = QtGui.QLineEdit(self.centralwidget)
        self.openbasediffline.setObjectName("openbasediffline")
        self.gridLayout_3.addWidget(self.openbasediffline, 1, 1, 1, 1)
        self.autochk = QtGui.QCheckBox(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.autochk.sizePolicy().hasHeightForWidth())
        self.autochk.setSizePolicy(sizePolicy)
        self.autochk.setObjectName("autochk")
        self.gridLayout_3.addWidget(self.autochk, 1, 6, 1, 1)
        self.autogrp = QtGui.QGroupBox(self.centralwidget)
        self.autogrp.setTitle("")
        self.autogrp.setObjectName("autogrp")
        self.gridLayout_2 = QtGui.QGridLayout(self.autogrp)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label_4 = QtGui.QLabel(self.autogrp)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setObjectName("label_4")
        self.gridLayout_2.addWidget(self.label_4, 0, 0, 1, 1)
        self.openspin = QtGui.QDoubleSpinBox(self.autogrp)
        self.openspin.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.openspin.setDecimals(1)
        self.openspin.setSingleStep(0.2)
        self.openspin.setProperty("value", 10.0)
        self.openspin.setObjectName("openspin")
        self.gridLayout_2.addWidget(self.openspin, 0, 1, 1, 1)
        self.label_5 = QtGui.QLabel(self.autogrp)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy)
        self.label_5.setObjectName("label_5")
        self.gridLayout_2.addWidget(self.label_5, 0, 2, 1, 1)
        self.closespin = QtGui.QDoubleSpinBox(self.autogrp)
        self.closespin.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.closespin.setDecimals(1)
        self.closespin.setSingleStep(0.2)
        self.closespin.setProperty("value", 15.0)
        self.closespin.setObjectName("closespin")
        self.gridLayout_2.addWidget(self.closespin, 0, 3, 1, 1)
        self.label_8 = QtGui.QLabel(self.autogrp)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_8.sizePolicy().hasHeightForWidth())
        self.label_8.setSizePolicy(sizePolicy)
        self.label_8.setObjectName("label_8")
        self.gridLayout_2.addWidget(self.label_8, 0, 4, 1, 1)
        self.opentimespin = QtGui.QSpinBox(self.autogrp)
        self.opentimespin.setProperty("value", 2)
        self.opentimespin.setObjectName("opentimespin")
        self.gridLayout_2.addWidget(self.opentimespin, 0, 5, 1, 1)
        self.label_9 = QtGui.QLabel(self.autogrp)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_9.sizePolicy().hasHeightForWidth())
        self.label_9.setSizePolicy(sizePolicy)
        self.label_9.setObjectName("label_9")
        self.gridLayout_2.addWidget(self.label_9, 0, 6, 1, 1)
        self.triggercountspin = QtGui.QSpinBox(self.autogrp)
        self.triggercountspin.setProperty("value", 2)
        self.triggercountspin.setObjectName("triggercountspin")
        self.gridLayout_2.addWidget(self.triggercountspin, 0, 7, 1, 1)
        self.label_10 = QtGui.QLabel(self.autogrp)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_10.sizePolicy().hasHeightForWidth())
        self.label_10.setSizePolicy(sizePolicy)
        self.label_10.setObjectName("label_10")
        self.gridLayout_2.addWidget(self.label_10, 0, 8, 1, 1)
        self.gridLayout_3.addWidget(self.autogrp, 2, 0, 1, 7)
        self.openbtn = QtGui.QPushButton(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.openbtn.sizePolicy().hasHeightForWidth())
        self.openbtn.setSizePolicy(sizePolicy)
        self.openbtn.setObjectName("openbtn")
        self.gridLayout_3.addWidget(self.openbtn, 3, 0, 1, 2)
        spacerItem = QtGui.QSpacerItem(451, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_3.addItem(spacerItem, 3, 2, 1, 4)
        self.closebtn = QtGui.QPushButton(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.closebtn.sizePolicy().hasHeightForWidth())
        self.closebtn.setSizePolicy(sizePolicy)
        self.closebtn.setObjectName("closebtn")
        self.gridLayout_3.addWidget(self.closebtn, 3, 6, 1, 1)
        self.label_6 = QtGui.QLabel(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy)
        self.label_6.setObjectName("label_6")
        self.gridLayout_3.addWidget(self.label_6, 1, 3, 1, 1)
        self.closebasediffline = QtGui.QLineEdit(self.centralwidget)
        self.closebasediffline.setObjectName("closebasediffline")
        self.gridLayout_3.addWidget(self.closebasediffline, 1, 4, 1, 1)
        self.warnchk = QtGui.QCheckBox(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.warnchk.sizePolicy().hasHeightForWidth())
        self.warnchk.setSizePolicy(sizePolicy)
        self.warnchk.setObjectName("warnchk")
        self.gridLayout_3.addWidget(self.warnchk, 1, 5, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 458, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "股指期货跨期套利", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("MainWindow", "跨期组合", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("MainWindow", "建仓基差", None, QtGui.QApplication.UnicodeUTF8))
        self.autochk.setText(QtGui.QApplication.translate("MainWindow", "自动", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("MainWindow", "建仓点", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("MainWindow", "平仓点", None, QtGui.QApplication.UnicodeUTF8))
        self.label_8.setText(QtGui.QApplication.translate("MainWindow", "建仓次数", None, QtGui.QApplication.UnicodeUTF8))
        self.label_9.setText(QtGui.QApplication.translate("MainWindow", "触发条件", None, QtGui.QApplication.UnicodeUTF8))
        self.label_10.setText(QtGui.QApplication.translate("MainWindow", "次", None, QtGui.QApplication.UnicodeUTF8))
        self.openbtn.setText(QtGui.QApplication.translate("MainWindow", "开仓", None, QtGui.QApplication.UnicodeUTF8))
        self.closebtn.setText(QtGui.QApplication.translate("MainWindow", "平仓", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("MainWindow", "平仓基差", None, QtGui.QApplication.UnicodeUTF8))
        self.warnchk.setText(QtGui.QApplication.translate("MainWindow", "报警", None, QtGui.QApplication.UnicodeUTF8))
