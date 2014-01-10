import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from crabmonui import Ui_crabmainwin
from flamelib import TBookLib, getstore, getpubsub
import flaredef as fdef
import config

class crabmonwin(QMainWindow, Ui_crabmainwin):
    def __init__(self, store, pubsub):
        QMainWindow.__init__(self)
        self.store = store
        self.pubsub = pubsub
        self.tblibs = {}
        self.strat2tb = {}
        self.curstrat = None

    def setup(self):
        self.setupUi(self)

        tb2strat = self.store.hgetall(fdef.STRATTBMAP)
        self.strat2tb = {tb2strat[k]:k for k in tb2strat}
        for s in self.strat2tb:
            self.stratcmbo.addItem(QString(s))
        self.stratcmbo.setCurrentIndex(0)
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
        tblib = self.gettblib(self.curstrat)
        self.tbnameline.setText(QString(tbname))


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

    ui = crabmonwin(store, pubsub)
    ui.setup()
    ui.show()

    app.exec_()

if __name__=="__main__":
    main(sys.argv)
