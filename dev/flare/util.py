import cPickle as pickle
from prettytable import PrettyTable
from PyQt4.QtCore import *

class Record(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

    def __getstate__(self):
        return self

    def __setstate__(self, state):
        self = state

    def dump(self):
        return pickle.dumps(self, -1)

    @staticmethod
    def load(s):
        return pickle.loads(s)

    def __str__(self):
        # TODO: unicode seems not work.
        return u', '.join( u': '.join((unicode(k),unicode(self[k]))) for k in self )

def printdictdict(d, rowkey, colkey):
    ck = [x for x in colkey]
    tbl = PrettyTable(ck)
    tbl.padding_width = 0
    for rk in rowkey:
        row = [d[rk][x] for x in colkey]
        tbl.add_row(row)
    print tbl

class listofdictTableModel(QAbstractTableModel):
    def __init__(self, colname, colnamemap, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.data = []
        self.colname = colname
        self.colnamemap = colnamemap

    def rowCount(self, parent=None):
        return len(self.data)

    def columnCount(self, parent=None):
        return len(self.colname)

    def addrows(self, newrows):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount()+len(newrows)-1)
        self.data.extend(newrows)
        self.endInsertRows()

    def clean(self):
        if self.rowCount() > 0:
            self.beginRemoveRows(QModelIndex(), 0, self.rowCount()-1)
            del self.data[0:]
            self.endRemoveRows()

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            hname = self.colname[section]
            try:
                hname = self.colnamemap[hname]
            except KeyError:
                pass
            return QVariant(hname)
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return QVariant(str(section + 1))
        return QVariant()

    def data(self, index, role):
        if not index.isValid():
            return QVariant()

        rowkey = index.row()
        columnkey = self.colname[index.column()]
        if role == Qt.DisplayRole:
            try:
                rawdata = self.data[rowkey][columnkey]
                if isinstance(rawdata, float):
                    rawdata = "%0.3f" % rawdata
                elif not isinstance(rawdata, unicode):# expect rawdata as numbers here
                    rawdata = str(rawdata)
                celldata = QString(rawdata)
            except KeyError:
                return QVariant()
            return QVariant(celldata)

        return QVariant()

    @pyqtSlot(int)
    def updaterow(self, rowindex):
        self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                self.index(rowindex,0),
                self.index(rowindex, len(self.colname)-1))

    @pyqtSlot()
    def updateall(self):
        self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                self.index(0,0),
                self.index(self.rowCount()-1, len(self.colname)-1))

