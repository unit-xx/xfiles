# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'login.ui'
#
# Created: Thu Jun 03 13:04:55 2010
#      by: PyQt4 UI code generator 4.7.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_logindlg(object):
    def setupUi(self, logindlg):
        logindlg.setObjectName("logindlg")
        logindlg.resize(298, 313)
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
        self.label_9 = QtGui.QLabel(self.groupBox)
        self.label_9.setObjectName("label_9")
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label_9)
        self.servaddr = QtGui.QLineEdit(self.groupBox)
        self.servaddr.setObjectName("servaddr")
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.servaddr)
        self.label_10 = QtGui.QLabel(self.groupBox)
        self.label_10.setObjectName("label_10")
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_10)
        self.servport = QtGui.QLineEdit(self.groupBox)
        self.servport.setObjectName("servport")
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.servport)
        self.label_8 = QtGui.QLabel(self.groupBox)
        self.label_8.setObjectName("label_8")
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.label_8)
        self.account = QtGui.QLineEdit(self.groupBox)
        self.account.setObjectName("account")
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.account)
        self.label_7 = QtGui.QLabel(self.groupBox)
        self.label_7.setObjectName("label_7")
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.label_7)
        self.passwd = QtGui.QLineEdit(self.groupBox)
        self.passwd.setEchoMode(QtGui.QLineEdit.Password)
        self.passwd.setObjectName("passwd")
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.passwd)
        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 3)
        self.groupBox_2 = QtGui.QGroupBox(logindlg)
        self.groupBox_2.setObjectName("groupBox_2")
        self.formLayout_2 = QtGui.QFormLayout(self.groupBox_2)
        self.formLayout_2.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout_2.setObjectName("formLayout_2")
        self.label_13 = QtGui.QLabel(self.groupBox_2)
        self.label_13.setObjectName("label_13")
        self.formLayout_2.setWidget(0, QtGui.QFormLayout.LabelRole, self.label_13)
        self.servaddr_jsd = QtGui.QLineEdit(self.groupBox_2)
        self.servaddr_jsd.setObjectName("servaddr_jsd")
        self.formLayout_2.setWidget(0, QtGui.QFormLayout.FieldRole, self.servaddr_jsd)
        self.label_11 = QtGui.QLabel(self.groupBox_2)
        self.label_11.setObjectName("label_11")
        self.formLayout_2.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_11)
        self.servport_jsd = QtGui.QLineEdit(self.groupBox_2)
        self.servport_jsd.setObjectName("servport_jsd")
        self.formLayout_2.setWidget(1, QtGui.QFormLayout.FieldRole, self.servport_jsd)
        self.label_14 = QtGui.QLabel(self.groupBox_2)
        self.label_14.setObjectName("label_14")
        self.formLayout_2.setWidget(2, QtGui.QFormLayout.LabelRole, self.label_14)
        self.account_jsd = QtGui.QLineEdit(self.groupBox_2)
        self.account_jsd.setObjectName("account_jsd")
        self.formLayout_2.setWidget(2, QtGui.QFormLayout.FieldRole, self.account_jsd)
        self.label_12 = QtGui.QLabel(self.groupBox_2)
        self.label_12.setObjectName("label_12")
        self.formLayout_2.setWidget(3, QtGui.QFormLayout.LabelRole, self.label_12)
        self.passwd_jsd = QtGui.QLineEdit(self.groupBox_2)
        self.passwd_jsd.setEchoMode(QtGui.QLineEdit.Password)
        self.passwd_jsd.setObjectName("passwd_jsd")
        self.formLayout_2.setWidget(3, QtGui.QFormLayout.FieldRole, self.passwd_jsd)
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
        self.groupBox.setTitle(QtGui.QApplication.translate("logindlg", "股票账号", None, QtGui.QApplication.UnicodeUTF8))
        self.label_9.setText(QtGui.QApplication.translate("logindlg", "服务器地址", None, QtGui.QApplication.UnicodeUTF8))
        self.label_10.setText(QtGui.QApplication.translate("logindlg", "端口", None, QtGui.QApplication.UnicodeUTF8))
        self.label_8.setText(QtGui.QApplication.translate("logindlg", "资金账号", None, QtGui.QApplication.UnicodeUTF8))
        self.label_7.setText(QtGui.QApplication.translate("logindlg", "密码", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_2.setTitle(QtGui.QApplication.translate("logindlg", "股指期货账号", None, QtGui.QApplication.UnicodeUTF8))
        self.label_13.setText(QtGui.QApplication.translate("logindlg", "服务器地址", None, QtGui.QApplication.UnicodeUTF8))
        self.label_11.setText(QtGui.QApplication.translate("logindlg", "端口", None, QtGui.QApplication.UnicodeUTF8))
        self.label_14.setText(QtGui.QApplication.translate("logindlg", "股指账号", None, QtGui.QApplication.UnicodeUTF8))
        self.label_12.setText(QtGui.QApplication.translate("logindlg", "密码", None, QtGui.QApplication.UnicodeUTF8))
        self.ok.setText(QtGui.QApplication.translate("logindlg", "确定", None, QtGui.QApplication.UnicodeUTF8))
        self.cancel.setText(QtGui.QApplication.translate("logindlg", "取消", None, QtGui.QApplication.UnicodeUTF8))
