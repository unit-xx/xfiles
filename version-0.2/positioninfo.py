# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'positioninfo.ui'
#
# Created: Wed May 12 09:25:12 2010
#      by: PyQt4 UI code generator 4.7.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_positioninfodlg(object):
    def setupUi(self, positioninfodlg):
        positioninfodlg.setObjectName("positioninfodlg")
        positioninfodlg.resize(354, 241)
        self.gridLayout = QtGui.QGridLayout(positioninfodlg)
        self.gridLayout.setObjectName("gridLayout")
        self.groupBox = QtGui.QGroupBox(positioninfodlg)
        self.groupBox.setObjectName("groupBox")
        self.formLayout = QtGui.QFormLayout(self.groupBox)
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName("formLayout")
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label_2)
        self.totalcost = QtGui.QLineEdit(self.groupBox)
        self.totalcost.setObjectName("totalcost")
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.totalcost)
        self.label_3 = QtGui.QLabel(self.groupBox)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_3)
        self.mktval = QtGui.QLineEdit(self.groupBox)
        self.mktval.setObjectName("mktval")
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.mktval)
        self.label = QtGui.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.label)
        self.profitval = QtGui.QLineEdit(self.groupBox)
        self.profitval.setObjectName("profitval")
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.profitval)
        self.label_4 = QtGui.QLabel(self.groupBox)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.label_4)
        self.profitper = QtGui.QLineEdit(self.groupBox)
        self.profitper.setObjectName("profitper")
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.profitper)
        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 3)
        spacerItem = QtGui.QSpacerItem(171, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 1, 0, 1, 1)
        self.refresh = QtGui.QPushButton(positioninfodlg)
        self.refresh.setObjectName("refresh")
        self.gridLayout.addWidget(self.refresh, 1, 1, 1, 1)
        self.ok = QtGui.QPushButton(positioninfodlg)
        self.ok.setObjectName("ok")
        self.gridLayout.addWidget(self.ok, 1, 2, 1, 1)

        self.retranslateUi(positioninfodlg)
        QtCore.QMetaObject.connectSlotsByName(positioninfodlg)

    def retranslateUi(self, positioninfodlg):
        positioninfodlg.setWindowTitle(QtGui.QApplication.translate("positioninfodlg", "持仓统计", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("positioninfodlg", "持仓信息", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("positioninfodlg", "买入成本：", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("positioninfodlg", "市值：", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("positioninfodlg", "盈亏值：", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("positioninfodlg", "盈亏比：", None, QtGui.QApplication.UnicodeUTF8))
        self.refresh.setText(QtGui.QApplication.translate("positioninfodlg", "刷新", None, QtGui.QApplication.UnicodeUTF8))
        self.ok.setText(QtGui.QApplication.translate("positioninfodlg", "确定", None, QtGui.QApplication.UnicodeUTF8))

