import cPickle as pickle
from threading import RLock

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
        s = ', '.join( ': '.join((str(k),str(self[k]))) for k in self )
        return s#.encode('utf-8')

    __repr__ = __str__

def printdictdict(d, rowkey, colkey):
    ck = [x for x in colkey]
    tbl = PrettyTable(ck)
    tbl.padding_width = 0
    for rk in rowkey:
        row = [d[rk][x] for x in colkey]
        tbl.add_row(row)
    print tbl

class listofdictTableModel(QAbstractTableModel):
    def __init__(self, keyname, colname, colnamemap, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.data = []
        self.keys = []
        self.lock = RLock()
        self.keyname = keyname
        self.colname = colname
        self.colnamemap = colnamemap

    def rowCount(self, parent=None):
        with self.lock:
            ret = len(self.data)
        return ret

    def columnCount(self, parent=None):
        with self.lock:
            ret = len(self.colname)
        return ret

    @pyqtSlot(str)
    def updaterows(self, newrows):
        # add a new row or update an existing row.
        print type(newrows)
        print newrows
        with self.lock:
            for row in newrows:
                if isinstance(row, list):
                    r = row
                else:
                    try:
                        r = pickle.loads(row)
                    except pickle.PickleError:
                        pass
                    print row
                    return

                try:
                    k = r[self.keyname]
                    if k in self.keys:
                        # existing key
                        i = self.keys.index(k)
                        self.data[i].update(r)
                        self.refreshrow(i)
                    else:
                        # a new key
                        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
                        self.keys.append(k)
                        self.data.append(r)
                        self.endInsertRows()
                except KeyError:
                    pass

    def clean(self):
        if self.rowCount() > 0:
            self.beginRemoveRows(QModelIndex(), 0, self.rowCount()-1)
            with self.lock:
                del self.data[0:]
                del self.keys[0:]
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
    def refreshrow(self, rowindex):
        self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                self.index(rowindex,0),
                self.index(rowindex, len(self.colname)-1))

    @pyqtSlot()
    def refreshall(self):
        self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                self.index(0,0),
                self.index(self.rowCount()-1, len(self.colname)-1))

