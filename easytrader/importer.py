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
            print celldata
            return QVariant(celldata)
        except KeyError:
            return QVariant()

class PortfolioPreviewModel(QAbstractTableModel):
    def __init__(self, header, pdata, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.header = header
        self.pdata = pdata

    def rowCount(self, parent):
        print "row", len(self.pdata)
        print self.pdata
        return len(self.pdata)

    def columnCount(self, parent):
        print "column", len(self.header)
        print self.pdata
        return len(self.header)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.header[section])
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return QVariant(str(section + 1))
        return QVariant()

    def data(self, index, role):
        # TODO: data is not called
        print "oh"
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        try:
            celldata = self.pdata[index.row()][index.column()]
            print celldata
            return QVariant(celldata)
        except KeyError:
            return QVariant()

class importer:
    def __init__(self, ui, dialog):
        self.ui = ui
        self.dialog = dialog
        self.my_array = [['00','01','02', '03'],
                ['10','11','12', '13'], ['20','21','22', '23']]

        # 'p' for portfolio
        self.plistdata = list() # should be list of list
        self.plistattr = [u"组合名称", u"创建时间"]
        self.plistmodel = PortfolioListModel(self.plistattr, self.plistdata)
        self.ui.portfolio_list.setModel(self.plistmodel)

        self.ppreviewdata = list()
        self.ppreviewattr = [u"市场代码", u"股票代码", u"股票名称", u"股票数量"]
        self.ppreviewmodel = PortfolioPreviewModel(self.ppreviewattr, self.ppreviewdata)
        #self.ppreviewmodel = PortfolioPreviewModel(self.ppreviewattr, self.my_array)
        self.ui.portfolio_preview.setModel(self.ppreviewmodel)

        # TODO: init existing porfolios

    def onSelectFile(self):
        fn = QFileDialog.getOpenFileName(self.dialog, u"选择Excel", "", "*.xls")
        fn = unicode(fn)
        book = open_workbook(fn)
        self.book = book

        for n in [n.decode("GBK") for n in book.sheet_names()]:
            # TODO: delete old list first
            self.ui.sheetlist.addItem(n)

    def onSelectSheet(self, index):
        # update self.plistdata
        sheet = self.book.sheet_by_index(index)
        print sheet.ncols
        if sheet.ncols != 4:
            # TODO: show message
            return

        del self.ppreviewdata[0:]
        for row in range(sheet.nrows):
            values = []
            for col in range(sheet.ncols):
                c = sheet.cell(row,col)
                if c.ctype == XL_CELL_TEXT:
                    values.append(c.value)
                else:
                    values.append(str(c.value))
            self.ppreviewdata.append(values)

        if len(self.ppreviewdata) > 0:
            print len(self.ppreviewdata), len(self.ppreviewattr)
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
