# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ilogin.ui'
#
# Created: Thu Jun 17 12:46:04 2010
#      by: PyQt4 UI code generator 4.7.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_logindlg(object):
    def setupUi(self, logindlg):
        logindlg.setObjectName("logindlg")
        logindlg.resize(238, 209)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(logindlg.sizePolicy().hasHeightForWidth())
        logindlg.setSizePolicy(sizePolicy)
        logindlg.setSizeGripEnabled(False)
        self.gridLayout = QtGui.QGridLayout(logindlg)
        self.gridLayout.setObjectName("gridLayout")
        self.groupBox = QtGui.QGroupBox(logindlg)
        self.groupBox.setObjectName("groupBox")
        self.formLayout = QtGui.QFormLayout(self.groupBox)
        self.formLayout.setObjectName("formLayout")
        self.label_3 = QtGui.QLabel(self.groupBox)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label_3)
        self.accountstock = QtGui.QLineEdit(self.groupBox)
        self.accountstock.setObjectName("accountstock")
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.accountstock)
        self.label_4 = QtGui.QLabel(self.groupBox)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_4)
        self.passwdstock = QtGui.QLineEdit(self.groupBox)
        self.passwdstock.setEchoMode(QtGui.QLineEdit.Password)
        self.passwdstock.setObjectName("passwdstock")
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.passwdstock)
        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 3)
        self.groupBox_2 = QtGui.QGroupBox(logindlg)
        self.groupBox_2.setObjectName("groupBox_2")
        self.formLayout_2 = QtGui.QFormLayout(self.groupBox_2)
        self.formLayout_2.setObjectName("formLayout_2")
        self.label_5 = QtGui.QLabel(self.groupBox_2)
        self.label_5.setObjectName("label_5")
        self.formLayout_2.setWidget(0, QtGui.QFormLayout.LabelRole, self.label_5)
        self.accountsindex = QtGui.QLineEdit(self.groupBox_2)
        self.accountsindex.setObjectName("accountsindex")
        self.formLayout_2.setWidget(0, QtGui.QFormLayout.FieldRole, self.accountsindex)
        self.label_6 = QtGui.QLabel(self.groupBox_2)
        self.label_6.setObjectName("label_6")
        self.formLayout_2.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_6)
        self.passwdsindex = QtGui.QLineEdit(self.groupBox_2)
        self.passwdsindex.setEchoMode(QtGui.QLineEdit.Password)
        self.passwdsindex.setObjectName("passwdsindex")
        self.formLayout_2.setWidget(1, QtGui.QFormLayout.FieldRole, self.passwdsindex)
        self.gridLayout.addWidget(self.groupBox_2, 1, 0, 1, 3)
        spacerItem = QtGui.QSpacerItem(58, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 2, 0, 1, 1)
        self.ok = QtGui.QPushButton(logindlg)
        self.ok.setObjectName("ok")
        self.gridLayout.addWidget(self.ok, 2, 1, 1, 1)
        self.cancel = QtGui.QPushButton(logindlg)
        self.cancel.setObjectName("cancel")
        self.gridLayout.addWidget(self.cancel, 2, 2, 1, 1)

        self.retranslateUi(logindlg)
        QtCore.QMetaObject.connectSlotsByName(logindlg)

    def retranslateUi(self, logindlg):
        logindlg.setWindowTitle(QtGui.QApplication.translate("logindlg", "登陆", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("logindlg", "股票账户", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("logindlg", "资金账号", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("logindlg", "密码", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_2.setTitle(QtGui.QApplication.translate("logindlg", "股指期货账户", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("logindlg", "股指账号", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("logindlg", "密码", None, QtGui.QApplication.UnicodeUTF8))
        self.ok.setText(QtGui.QApplication.translate("logindlg", "确定", None, QtGui.QApplication.UnicodeUTF8))
        self.cancel.setText(QtGui.QApplication.translate("logindlg", "取消", None, QtGui.QApplication.UnicodeUTF8))

