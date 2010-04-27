# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'login.ui'
#
# Created: Tue Apr 27 16:36:27 2010
#      by: PyQt4 UI code generator 4.7.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_logindlg(object):
    def setupUi(self, logindlg):
        logindlg.setObjectName("logindlg")
        logindlg.resize(241, 145)
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
        self.gridLayout.addWidget(self.label, 0, 0, 1, 2)
        self.servaddr = QtGui.QLineEdit(logindlg)
        self.servaddr.setObjectName("servaddr")
        self.gridLayout.addWidget(self.servaddr, 0, 2, 1, 2)
        self.label_2 = QtGui.QLabel(logindlg)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 2)
        self.servport = QtGui.QLineEdit(logindlg)
        self.servport.setObjectName("servport")
        self.gridLayout.addWidget(self.servport, 1, 2, 1, 2)
        self.label_3 = QtGui.QLabel(logindlg)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 2)
        self.accout = QtGui.QLineEdit(logindlg)
        self.accout.setObjectName("accout")
        self.gridLayout.addWidget(self.accout, 2, 2, 1, 2)
        self.label_4 = QtGui.QLabel(logindlg)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 3, 0, 1, 2)
        self.passwd = QtGui.QLineEdit(logindlg)
        self.passwd.setEchoMode(QtGui.QLineEdit.Password)
        self.passwd.setObjectName("passwd")
        self.gridLayout.addWidget(self.passwd, 3, 2, 1, 2)
        spacerItem = QtGui.QSpacerItem(58, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 4, 0, 1, 1)
        self.ok = QtGui.QPushButton(logindlg)
        self.ok.setObjectName("ok")
        self.gridLayout.addWidget(self.ok, 4, 1, 1, 2)
        self.cancel = QtGui.QPushButton(logindlg)
        self.cancel.setObjectName("cancel")
        self.gridLayout.addWidget(self.cancel, 4, 3, 1, 1)

        self.retranslateUi(logindlg)
        QtCore.QMetaObject.connectSlotsByName(logindlg)

    def retranslateUi(self, logindlg):
        logindlg.setWindowTitle(QtGui.QApplication.translate("logindlg", "登陆", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("logindlg", "服务器地址", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("logindlg", "端口", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("logindlg", "资金账号", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("logindlg", "密码", None, QtGui.QApplication.UnicodeUTF8))
        self.ok.setText(QtGui.QApplication.translate("logindlg", "确定", None, QtGui.QApplication.UnicodeUTF8))
        self.cancel.setText(QtGui.QApplication.translate("logindlg", "取消", None, QtGui.QApplication.UnicodeUTF8))

