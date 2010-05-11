# -*- coding: utf-8 -*-

import sys
from datetime import datetime

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from importdiag import Ui_ImportDialog

from xlrd import open_workbook, XL_CELL_TEXT

class PortfolioListModel(QAbstractTableModel):
    def __init__(self, header, pdata, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.header = header
        self.pdata = pdata

    def rowCount(self, parent):
        return len(self.pdata)

    def columnCount(self, parent):
        return len(self.header)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.header[section])
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return QVariant(str(section + 1))
        return QVariant()

    def data(self, index, role):
        # TODO: data is not called
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        try:
            celldata = self.pdata[index.row()][index.column()]
            return QVariant(celldata)
        except KeyError:
            return QVariant()

class PortfolioPreviewModel(QAbstractTableModel):
    def __init__(self, header, pdata, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.header = header
        self.pdata = pdata

    def rowCount(self, parent):
        return len(self.pdata.ppreviewdata)

    def columnCount(self, parent):
        return len(self.header)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.header[section])
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return QVariant(str(section + 1))
        return QVariant()

    def data(self, index, role):
        # TODO: data is not called
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        try:
            celldata = self.pdata.ppreviewdata[index.row()][index.column()]
            return QVariant(celldata)
        except KeyError:
            return QVariant()

class importer:
    def __init__(self, ui, dialog):
        self.ui = ui
        self.dialog = dialog
        self.book = None

        # 'p' for portfolio
        self.plistdata = list() # should be list of list
        self.plistattr = [u"组合名称", u"创建时间"]
        self.plistmodel = PortfolioListModel(self.plistattr, self.plistdata)
        self.ui.portfolio_list.setModel(self.plistmodel)

        self.ppreviewdata = list()
        self.ppreviewattr = [u"市场代码", u"股票代码", u"股票名称", u"股票数量"]
        self.ppreviewmodel = PortfolioPreviewModel(self.ppreviewattr, self)
        self.ui.portfolio_preview.setModel(self.ppreviewmodel)

        # TODO: init existing porfolios

    def onSelectFile(self):
        fn = QFileDialog.getOpenFileName(self.dialog, u"选择Excel", "", "*.xls")
        fn = unicode(fn)
        book = open_workbook(fn)
        self.book = book

        self.ui.sheetlist.clear()
        #for n in [n.decode(book.encoding) for n in book.sheet_names()]:
        for n in book.sheet_names():
            self.ui.sheetlist.addItem(n)

    def onSelectSheet(self, index):
        # update self.plistdata
        sheet = self.book.sheet_by_index(index)
        #if sheet.ncols != 4:
        #    # TODO: show message
        #    return

        # delete old data
        self.ppreviewmodel.beginRemoveRows(QModelIndex(), 0, len(self.ppreviewdata) - 1)
        del self.ppreviewdata[0:]
        self.ppreviewmodel.endRemoveRows()

        newdata = []
        for row in range(sheet.nrows):
            values = []
            for col in range(sheet.ncols):
                c = sheet.cell(row,col)
                if c.ctype == XL_CELL_TEXT:
                    values.append(c.value)
                else:
                    values.append(str(c.value))
            newdata.append(values)

        if newdata != []:
            self.ppreviewmodel.beginInsertRows(QModelIndex(), 0, len(newdata) - 1)
            self.ppreviewdata.extend(newdata)
            self.ppreviewmodel.endInsertRows()

        self.ppreviewmodel.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                self.ppreviewmodel.index(0,0),
                self.ppreviewmodel.index(len(self.ppreviewdata) - 1,
                    len(self.ppreviewattr) - 1))

    def onDoImport(self):
        pass

    def onCancel(self):
        self.dialog.close()
        pass

def main(args):
    app = QApplication(args)
    dialog = QDialog()
    ui = Ui_ImportDialog()
    ui.setupUi(dialog)

    # connect signals of dialog with importer's handlers
    i = importer(ui, dialog)
    dialog.connect(ui.selectfile, SIGNAL("clicked()"), i.onSelectFile)
    dialog.connect(ui.cancelimport, SIGNAL("clicked()"), i.onCancel)
    dialog.connect(ui.sheetlist, SIGNAL("currentIndexChanged(int)"), i.onSelectSheet)

    dialog.show()
    app.exec_()

if __name__=="__main__":
    main(sys.argv)

# set ++encoding="utf-8"
