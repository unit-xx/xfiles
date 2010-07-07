import sys
import os
import ConfigParser

from threading import Thread
import logging, logging.config
from struct import pack, unpack

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import jsd

# 1 gui thread
# 2 worker thread for long/short each stock index
# 1 update thread for monitor prices and diffs, and issue instructions
# auotmatically, if set.

class StockIndexModel(QAbstractTableModel):
    def __init__(self, portfolio, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.portfolio = portfolio

    def rowCount(self, parent):
        return 1

    def columnCount(self, parent):
        return len(self.portfolio.sindexmodelattr)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            hname = self.portfolio.sindexmodelattr[section]
            try:
                hname = self.portfolio.sindexattrnamemap[hname]
            except KeyError:
                pass
            return QVariant(hname)
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return QVariant(str(section + 1))
        return QVariant()

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        columnkey = self.portfolio.sindexmodelattr[index.column()]
        try:
            rawdata = self.portfolio.sindexinfo[columnkey]
            if not isinstance(rawdata, unicode):# expect rawdata as numbers here
                rawdata = str(rawdata)
            celldata = QString(rawdata)
            return QVariant(celldata)
        except KeyError:
            return QVariant()

    @pyqtSlot()
    def updaterow(self):
        self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                self.index(0,0),
                self.index(0, len(self.portfolio.sindexmodelattr)-1))


