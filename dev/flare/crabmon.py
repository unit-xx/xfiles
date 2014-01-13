import sys
from datetime import datetime

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from crabmonui import Ui_crabmainwin
from flamelib import TBookLib, getstore, getpubsub
from util import listofdictTableModel
import flaredef as fdef
import config

class crabmonwin(QMainWindow, Ui_crabmainwin):
    def __init__(self, store, pubsub, mycfg):
        QMainWindow.__init__(self)
        self.store = store
        self.pubsub = pubsub
        self.tblibs = {}
        self.strat2tb = {}
        self.curstrat = None
        self.posmodel = listofdictTableModel([getattr(fdef, x) for x in mycfg['poskeys'].split()], {})
        self.ordermodel = listofdictTableModel([getattr(fdef, x) for x in mycfg['orderkeys'].split()], {})

    def setup(self):
        self.setupUi(self)

        self.positiontbl.setModel(self.posmodel)
        self.ordertbl.setModel(self.ordermodel)

        self.reloadstrat()

        return True

    def gettblib(self, strat):
        ret = None
        try:
            ret = self.tblibs[strat]
        except KeyError:
            tblib = TBookLib(self.store, self.strat2tb[strat])
            if not tblib.setup():
                tblib = None
            self.tblibs[strat] = tblib
            ret = tblib
        return ret

    @pyqtSlot(QString)
    def on_stratcmbo_currentIndexChanged(self, strat):
        self.curstrat = str(strat)
        tbname = self.strat2tb[self.curstrat]
        self.tbnameline.setText(QString(tbname))

        self.reloadpos()
        self.reloadorder()

    def reloadstrat(self, newindex=0):
        tb2strat = self.store.hgetall(fdef.STRATTBMAP)
        self.strat2tb = {tb2strat[k]:k for k in tb2strat}

        self.stratcmbo.clear()
        for s in self.strat2tb:
            self.stratcmbo.addItem(QString(s))
        self.stratcmbo.setCurrentIndex(newindex)

    def reloadpos(self):
        tblib = self.gettblib(self.curstrat)
        if tblib is None:
            return

        poskeys = tblib.getallposkey()
        poskeys.sort()
        newpos = []
        for pk in poskeys:
            newpos.append(tblib.getposition(pk))

        self.posmodel.clean()
        self.posmodel.addrows(newpos)
        #self.posmodel.updateall()

    def reloadorder(self):
        tblib = self.gettblib(self.curstrat)
        if tblib is None:
            return

        alloids = tblib.getalloid()
        neworders = []
        for oid in alloids:
            neworders.append(tblib.getorder(oid))
        neworders.sort(key=lambda x: datetime.strptime(x[fdef.KORDERDATE], config.GCONFIG['dateformat']))

        self.ordermodel.clean()
        self.ordermodel.addrows(neworders)
        #self.ordermodel.updateall()

def main(args):
    app = QApplication(args)

    mysec = 'crabmon'
    cfg = config.parseconfig()
    mycfg = cfg[mysec]

    storecfg = cfg[mycfg['store']]
    storecfg['port'] = int(storecfg['port'])
    storecfg['db'] = int(storecfg['db'])

    config.setuplogger(mysec)

    store = getstore(storecfg)
    pubsub = getpubsub(storecfg)

    ui = crabmonwin(store, pubsub, mycfg)
    ui.setup()
    ui.show()

    app.exec_()

if __name__=="__main__":
    main(sys.argv)
