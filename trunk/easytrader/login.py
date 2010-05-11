# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'login.ui'
#
# Created: Tue May 11 15:45:08 2010
#      by: PyQt4 UI code generator 4.7.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_logindlg(object):
    def setupUi(self, logindlg):
        logindlg.setObjectName("logindlg")
        logindlg.resize(240, 197)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(logindlg.sizePolicy().hasHeightForWidth())
        logindlg.setSizePolicy(sizePolicy)
        logindlg.setSizeGripEnabled(False)
        self.gridLayout = QtGui.QGridLayout(logindlg)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtGui.QLabel(logindlg)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.servaddr = QtGui.QLineEdit(logindlg)
        self.servaddr.setObjectName("servaddr")
        self.gridLayout.addWidget(self.servaddr, 0, 1, 1, 2)
        self.label_2 = QtGui.QLabel(logindlg)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.servport = QtGui.QLineEdit(logindlg)
        self.servport.setObjectName("servport")
        self.gridLayout.addWidget(self.servport, 1, 1, 1, 2)
        self.label_3 = QtGui.QLabel(logindlg)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.account = QtGui.QLineEdit(logindlg)
        self.account.setObjectName("account")
        self.gridLayout.addWidget(self.account, 2, 1, 1, 2)
        self.label_4 = QtGui.QLabel(logindlg)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 3, 0, 1, 1)
        self.passwd = QtGui.QLineEdit(logindlg)
        self.passwd.setEchoMode(QtGui.QLineEdit.Password)
        self.passwd.setObjectName("passwd")
        self.gridLayout.addWidget(self.passwd, 3, 1, 1, 2)
        self.label_5 = QtGui.QLabel(logindlg)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 4, 0, 1, 1)
        self.shdbfn = QtGui.QLineEdit(logindlg)
        self.shdbfn.setEchoMode(QtGui.QLineEdit.Normal)
        self.shdbfn.setObjectName("shdbfn")
        self.gridLayout.addWidget(self.shdbfn, 4, 1, 1, 2)
        self.label_6 = QtGui.QLabel(logindlg)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 5, 0, 1, 1)
        self.szdbfn = QtGui.QLineEdit(logindlg)
        self.szdbfn.setEchoMode(QtGui.QLineEdit.Normal)
        self.szdbfn.setObjectName("szdbfn")
        self.gridLayout.addWidget(self.szdbfn, 5, 1, 1, 2)
        spacerItem = QtGui.QSpacerItem(58, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 6, 0, 1, 1)
        self.ok = QtGui.QPushButton(logindlg)
        self.ok.setObjectName("ok")
        self.gridLayout.addWidget(self.ok, 6, 1, 1, 1)
        self.cancel = QtGui.QPushButton(logindlg)
        self.cancel.setObjectName("cancel")
        self.gridLayout.addWidget(self.cancel, 6, 2, 1, 1)

        self.retranslateUi(logindlg)
        QtCore.QMetaObject.connectSlotsByName(logindlg)

    def retranslateUi(self, logindlg):
        logindlg.setWindowTitle(QtGui.QApplication.translate("logindlg", "登陆", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("logindlg", "服务器地址", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("logindlg", "端口", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("logindlg", "资金账号", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("logindlg", "密码", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("logindlg", "上海行情", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("logindlg", "深圳行情", None, QtGui.QApplication.UnicodeUTF8))
        self.ok.setText(QtGui.QApplication.translate("logindlg", "确定", None, QtGui.QApplication.UnicodeUTF8))
        self.cancel.setText(QtGui.QApplication.translate("logindlg", "取消", None, QtGui.QApplication.UnicodeUTF8))

