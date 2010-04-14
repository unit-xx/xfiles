# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'importdiag.ui'
#
# Created: Wed Apr 14 15:18:24 2010
#      by: PyQt4 UI code generator 4.7.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_ImportDialog(object):
    def setupUi(self, ImportDialog):
        ImportDialog.setObjectName("ImportDialog")
        ImportDialog.resize(817, 530)
        self.gridLayout = QtGui.QGridLayout(ImportDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.selectfile = QtGui.QPushButton(ImportDialog)
        self.selectfile.setObjectName("selectfile")
        self.gridLayout.addWidget(self.selectfile, 1, 0, 1, 1)
        self.splitter = QtGui.QSplitter(ImportDialog)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setObjectName("splitter")
        self.portfolio_list = QtGui.QTableView(self.splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.portfolio_list.sizePolicy().hasHeightForWidth())
        self.portfolio_list.setSizePolicy(sizePolicy)
        self.portfolio_list.setObjectName("portfolio_list")
        self.portfolio_preview = QtGui.QTableView(self.splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(5)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.portfolio_preview.sizePolicy().hasHeightForWidth())
        self.portfolio_preview.setSizePolicy(sizePolicy)
        self.portfolio_preview.setObjectName("portfolio_preview")
        self.gridLayout.addWidget(self.splitter, 0, 1, 9, 2)
        self.label = QtGui.QLabel(ImportDialog)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 2, 0, 1, 1)
        self.sheetlist = QtGui.QComboBox(ImportDialog)
        self.sheetlist.setObjectName("sheetlist")
        self.gridLayout.addWidget(self.sheetlist, 3, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(17, 385, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 4, 0, 1, 1)
        self.doimport = QtGui.QPushButton(ImportDialog)
        self.doimport.setObjectName("doimport")
        self.gridLayout.addWidget(self.doimport, 8, 0, 1, 1)
        self.cancelimport = QtGui.QPushButton(ImportDialog)
        self.cancelimport.setObjectName("cancelimport")
        self.gridLayout.addWidget(self.cancelimport, 9, 0, 1, 1)
        self.infoline = QtGui.QLineEdit(ImportDialog)
        self.infoline.setFrame(True)
        self.infoline.setReadOnly(True)
        self.infoline.setObjectName("infoline")
        self.gridLayout.addWidget(self.infoline, 9, 2, 1, 1)
        self.label_2 = QtGui.QLabel(ImportDialog)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 9, 1, 1, 1)
        self.portfolio_name = QtGui.QLineEdit(ImportDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.portfolio_name.sizePolicy().hasHeightForWidth())
        self.portfolio_name.setSizePolicy(sizePolicy)
        self.portfolio_name.setObjectName("portfolio_name")
        self.gridLayout.addWidget(self.portfolio_name, 6, 0, 1, 1)
        self.label_3 = QtGui.QLabel(ImportDialog)
        self.label_3.setAlignment(QtCore.Qt.AlignCenter)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 5, 0, 1, 1)

        self.retranslateUi(ImportDialog)
        QtCore.QMetaObject.connectSlotsByName(ImportDialog)

    def retranslateUi(self, ImportDialog):
        ImportDialog.setWindowTitle(QtGui.QApplication.translate("ImportDialog", "导入组合", None, QtGui.QApplication.UnicodeUTF8))
        self.selectfile.setText(QtGui.QApplication.translate("ImportDialog", "选择Excel文件", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("ImportDialog", "选择工作表", None, QtGui.QApplication.UnicodeUTF8))
        self.doimport.setText(QtGui.QApplication.translate("ImportDialog", "保存组合", None, QtGui.QApplication.UnicodeUTF8))
        self.cancelimport.setText(QtGui.QApplication.translate("ImportDialog", "取消", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("ImportDialog", "操作信息", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("ImportDialog", "组合名称", None, QtGui.QApplication.UnicodeUTF8))

