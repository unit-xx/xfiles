# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'deliverdlg.ui'
#
# Created: Thu Jun 10 15:04:52 2010
#      by: PyQt4 UI code generator 4.7.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_deliverdlg(object):
    def setupUi(self, deliverdlg):
        deliverdlg.setObjectName("deliverdlg")
        deliverdlg.resize(286, 136)
        self.gridLayout_2 = QtGui.QGridLayout(deliverdlg)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.groupBox = QtGui.QGroupBox(deliverdlg)
        self.groupBox.setTitle("")
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtGui.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.diffline = QtGui.QLineEdit(self.groupBox)
        self.diffline.setObjectName("diffline")
        self.gridLayout.addWidget(self.diffline, 2, 2, 1, 1)
        self.label_4 = QtGui.QLabel(self.groupBox)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 2, 0, 1, 2)
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 2)
        self.sindexcmb = QtGui.QComboBox(self.groupBox)
        self.sindexcmb.setObjectName("sindexcmb")
        self.gridLayout.addWidget(self.sindexcmb, 1, 1, 1, 1)
        self.sindexline = QtGui.QLineEdit(self.groupBox)
        self.sindexline.setObjectName("sindexline")
        self.gridLayout.addWidget(self.sindexline, 1, 2, 1, 1)
        self.label_3 = QtGui.QLabel(self.groupBox)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)
        self.hs300avgline = QtGui.QLineEdit(self.groupBox)
        self.hs300avgline.setObjectName("hs300avgline")
        self.gridLayout.addWidget(self.hs300avgline, 0, 2, 1, 1)
        self.gridLayout_2.addWidget(self.groupBox, 0, 0, 1, 2)
        self.label = QtGui.QLabel(deliverdlg)
        self.label.setObjectName("label")
        self.gridLayout_2.addWidget(self.label, 1, 0, 1, 1)
        self.statusline = QtGui.QLineEdit(deliverdlg)
        self.statusline.setObjectName("statusline")
        self.gridLayout_2.addWidget(self.statusline, 1, 1, 1, 1)

        self.retranslateUi(deliverdlg)
        QtCore.QMetaObject.connectSlotsByName(deliverdlg)

    def retranslateUi(self, deliverdlg):
        deliverdlg.setWindowTitle(QtGui.QApplication.translate("deliverdlg", "股指交割价格", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("deliverdlg", "价差", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("deliverdlg", "沪深300算术平均", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("deliverdlg", "股指", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("deliverdlg", "当前状态", None, QtGui.QApplication.UnicodeUTF8))

