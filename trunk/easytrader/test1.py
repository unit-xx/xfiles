from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys
import threading
import random
import time

my_array = [['00','01','02'],
            ['10','11','12'],
            ['20','21','22']]

def update(w):
    while 1:
        my_array[0][0] = str(random.randint(0,10))
        print my_array[0][0]
        w.model.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"), 
                w.model.index(0,0), w.model.index(0,0))
        time.sleep(1)

def main():
    app = QApplication(sys.argv)
    w = MyWindow()
    threading.Thread(target=update, args=[w]).start()
    w.show()
    sys.exit(app.exec_())

class MyWindow(QWidget):
    def __init__(self, *args):
        QWidget.__init__(self, *args)

        tablemodel = MyTableModel(my_array, self)
        self.model = tablemodel
        tableview = QTableView()
        self.tableview = tableview
        tableview.setModel(tablemodel)

        layout = QVBoxLayout(self)
        layout.addWidget(tableview)
        self.setLayout(layout)

class MyTableModel(QAbstractTableModel):
    def __init__(self, datain, parent=None, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.arraydata = datain

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        return len(self.arraydata[0])

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        return QVariant(self.arraydata[index.row()][index.column()])

if __name__ == "__main__":
    main()

#$Id$
