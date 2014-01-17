import sys
from datetime import datetime
from threading import Thread, currentThread
import cPickle as pickle
import logging

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
        self.posmodel = listofdictTableModel(getattr(fdef, mycfg['poskey']), [getattr(fdef, x) for x in mycfg['poscolumn'].split()], {})
        self.ordermodel = listofdictTableModel(getattr(fdef, mycfg['orderkey']), [getattr(fdef, x) for x in mycfg['ordercolumn'].split()], {})

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
        try:
            self.pubsub.publish(fdef.CHNTFTBOOK, pickle.dumps((fdef.CMDUI, self.curstrat, self.curstrat), -1))
        except pickle.PickleError:
            pass

    def reloadstrat(self, newindex=0):
        tb2strat = self.store.hgetall(fdef.STRATTBMAP)
        self.strat2tb = {tb2strat[k]:k for k in tb2strat}

        self.stratcmbo.clear()
        for s in self.strat2tb:
            self.stratcmbo.addItem(QString(s))
        self.stratcmbo.setCurrentIndex(newindex)

    @pyqtSlot()
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
        self.posmodel.updaterows(newpos, [p[fdef.KPOSKEY] for p in newpos])
        #self.posmodel.updateall()

    @pyqtSlot()
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
        self.ordermodel.updaterows(neworders, [o[fdef.KOID] for o in neworders])
        #self.ordermodel.updateall()

class updater(Thread):
    def __init__(self, pubsub, win):
        Thread.__init__(self)
        self.pubsub = pubsub
        self.posmodel = win.posmodel
        self.ordermodel = win.ordermodel
        self.win = win
        self.curstrat = None

        self.runflag = True
        self.logger = logging.getLogger()
        self.name = self.__class__.__name__

    def setup(self):
        self.pubsub.subscribe(fdef.CHNTFTBOOK)
        self.pubsub.subscribe(fdef.CHHEARTBEAT)

    def stop(self):
        self.runflag = False

    def run(self):
        self.setup()

        while self.runflag:
            m = self.pubsub.listen()
            if m['channel'] == fdef.CHHEARTBEAT:
                continue

            try:
                cmd, strat, arg = pickle.loads(m['data'])
            except pickle.PickleError:
                continue

            try:
                if cmd==fdef.CMDUI:
                    self.curstrat = arg
                    QMetaObject.invokeMethod(self.win, 'reloadpos', Qt.QueuedConnection)
                    QMetaObject.invokeMethod(self.win, 'reloadorder', Qt.QueuedConnection)

                if strat==self.curstrat and cmd in (fdef.CMDNEWORDER, fdef.CMDUPDATEORDER):
                    oid = arg[0]
                    o = arg[1]
                    QMetaObject.invokeMethod(self.win.ordermodel,
                            'updaterows',
                            Qt.QueuedConnection,
                            Q_ARG(list, [o]),
                            Q_ARG(list, [oid])
                            )
                    QMetaObject.invokeMethod(self.win.ordertbl,
                            'scrollToBottom',
                            Qt.QueuedConnection
                            )

                elif strat==self.curstrat and cmd in (fdef.CMDUPDATEPOS, fdef.CMDNEWPOSITION):
                    poskey = arg[0]
                    p = arg[1]
                    QMetaObject.invokeMethod(self.win.posmodel,
                            'updaterows',
                            Qt.QueuedConnection,
                            Q_ARG(list, [p]),
                            Q_ARG(list, [poskey])
                            )
            except:
                self.logger.exception('exception at update UI %s, with arg %s', cmd, arg)
        self.logger.info('stop monitor.')

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
    if store is None or pubsub is None:
        raise Exception('connect to store or pubsub failed.')

    ui = crabmonwin(store, pubsub, mycfg)

    upd = updater(pubsub, ui)
    upd.start()

    ui.setup()
    ui.show()
    app.exec_()

    upd.stop()
    pubsub.publish(fdef.CHHEARTBEAT, 'stop monitor')

if __name__=="__main__":
    main(sys.argv)
# $Id$ 
