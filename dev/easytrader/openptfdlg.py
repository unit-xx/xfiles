# -*- coding: utf-8 -*-

from openptfui import Ui_Dialog
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import os
import sys
import glob
import shutil
from datetime import datetime

class ptfModel(QAbstractTableModel):
    def __init__(self, header, headermap, data, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.header = header
        self.headermap = headermap
        self.data = data

    def rowCount(self, parent):
        return len(self.data)

    def columnCount(self, parent):
        return len(self.header)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            hname = self.header[section]
            try:
                hname = self.headermap[hname]
            except KeyError:
                pass
            return QVariant(hname)
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return QVariant(str(section + 1))
        return QVariant()

    def data(self, index, role):
        # self.data is list of dict
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        try:
            rowindex = index.row()
            columnkey = self.header[index.column()]
            celldata = self.data[rowindex][columnkey]
        except IndexError, KeyError:
            return QVariant()
        return QVariant((celldata))

    @pyqtSlot(int)
    def updaterow(self, rowindex):
        self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                self.index(rowindex,0),
                self.index(rowindex,self.columnCount()-1))


class openptfdlg(QDialog, Ui_Dialog):
    def __init__(self, ptfpath):
        QDialog.__init__(self)
        self.ptfpath = ptfpath
        self.ptfattr = ["fn", "ptfname", "datetext", "ctime"]
        self.ptfshowattr = ["ptfname"]
        self.posshowattr = ["ptfname", "datetext"]
        self.attrmap = {
                "ptfname":u"组合名称",
                "datetext":u"建仓时间"
                }
        self.selectedfn = ""

    def setup(self):
        self.setupUi(self)

        ptfdata = self.genptfdata()
        posdata = self.genposdata()
        self.ptfdata = ptfdata
        self.posdata = posdata

        self.ptfmodel = ptfModel(self.ptfshowattr,
                self.attrmap, ptfdata)
        self.ptftable.setModel(self.ptfmodel)
        self.ptftable.resizeColumnsToContents()

        self.posmodel = ptfModel(self.posshowattr,
                self.attrmap, posdata)
        self.postable.setModel(self.posmodel)
        self.postable.resizeColumnsToContents()
        return True

    def genptfdata(self):
        data = []
        ptfns = glob.glob(os.path.join(self.ptfpath, "*.ptf"))
        for fn in ptfns:
            fn = fn.decode("gbk")
            item = {}
            item["fn"] = fn
            item["ptfname"] = os.path.basename(fn)[0:-4]
            item["ctime"] = int(os.path.getctime(fn))
            item["datetext"] = str(datetime.fromtimestamp(item["ctime"]))
            data.append(item)
            #print item

        data.sort(cmp=self.ptfcmp, reverse=True)
        return data

    def genposdata(self):
        data = []
        ptfns = glob.glob(os.path.join(self.ptfpath, "*.pos"))
        for fn in ptfns:
            fn = fn.decode("gbk")
            item = {}
            item["fn"] = fn
            item["ptfname"] = os.path.basename(fn)[0:-4]
            item["ctime"] = int(os.path.getctime(fn))
            item["datetext"] = str(datetime.fromtimestamp(item["ctime"]))
            data.append(item)
            #print item

        data.sort(cmp=self.ptfcmp, reverse=True)
        return data

    def ptfcmp(self, p1, p2):
        if p1["ptfname"] == p2["ptfname"]:
            if p1["ctime"] == p2["ctime"]:
                return 0
            elif p1["ctime"] < p2["ctime"]:
                return -1
            else:
                return 1
        elif p1["ptfname"] < p2["ptfname"]:
            return -1
        else:
            return 1

    @pyqtSlot()
    def on_ptfokbtn_clicked(self):
        rows = self.ptftable.selectedIndexes()
        if len(rows) == 0:
            QMessageBox.warning(None,
                    u"",
                    u"尚未选择组合。",
                    QMessageBox.Ok)
        else:
            ptfn = self.ptfdata[rows[0].row()]["fn"]
            ptfna = ptfn[0:-4]
            ptfnb = "pos"
            n = 0
            while 1:
                n += 1
                posfn = ".".join([ptfna, str(n), ptfnb])
                if not os.path.exists(posfn):
                    shutil.copy(ptfn, posfn)
                    self.selectedfn = posfn
                    break
            self.done(1)

    @pyqtSlot()
    def on_posokbtn_clicked(self):
        rows = self.postable.selectedIndexes()
        if len(rows) == 0:
            QMessageBox.warning(None,
                    u"",
                    u"尚未选择组合。",
                    QMessageBox.Ok)
        else:
            self.selectedfn = self.posdata[rows[0].row()]["fn"]
            self.done(1)

    @pyqtSlot()
    def on_ptfcancelbtn_clicked(self):
        self.done(0)

    @pyqtSlot()
    def on_poscancelbtn_clicked(self):
        self.done(0)

def main(args):
    app = QApplication(args)
    ptfdlg = openptfdlg("portfolio")
    if ptfdlg.setup():
        ptfdlg.show()
        ptfdlg.activateWindow()
        app.exec_()

if __name__=="__main__":
    main(sys.argv)

