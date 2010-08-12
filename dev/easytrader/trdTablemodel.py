#from PyQt4.QtGui import *
from PyQt4.QtCore import *

class dictdict(dict):
    def __getitem__(self, key):
        if not key in self:
            self.setdefault(key, dict())
        return dict.__getitem__(self, key)

class trdData:
    def __init__(self):
        self.data = dictdict()
        self.bgcolor = dictdict()
        self.colname = []
        self.colnamemap = dictdict()
        self.rowname = []

class TradeTableModel_dd(QAbstractTableModel):
    """
    dd for dict of dict
    """
    def __init__(self, modeldata, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.modeldata = modeldata
        """
        modeldata is a class with following fields:

        - data: dict of dict data
        - bgcolor: color spec for data cell background
        - colname: column names to be displayed in data
        - colnamemap: colname to its display name mapping
        - rowname: list of row keys, used for order rows 
        """
        self.data = modeldata.data
        self.bgcolor = modeldata.bgcolor
        self.colname = modeldata.colname
        self.colnamemap = modeldata.colnamemap
        self.rowname = modeldata.rowname

    def rowCount(self, parent):
        return len(self.rowname)

    def columnCount(self, parent):
        return len(self.colname)

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

        rowkey = self.rowname[index.row()]
        columnkey = self.colname[index.column()]
        if role == Qt.DisplayRole:
            try:
                rawdata = self.data[rowkey][columnkey]
                if not isinstance(rawdata, unicode):# expect rawdata as numbers here
                    rawdata = str(rawdata)
                celldata = QString(rawdata)
            except:
                return QVariant()
            return QVariant(celldata)
        elif role == Qt.BackgroundRole:
            try:
                c = self.bgcolor[rowkey][columnkey]
            except KeyError:
                pass
            return QVariant(c)

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
                self.index(len(self.rowname)-1, len(self.colname)-1))


