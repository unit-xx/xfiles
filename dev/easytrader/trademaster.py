# -*- coding: utf-8 -*-

import sys, os
import logging
import logging.config
import socket
import pickle
import SocketServer
import ConfigParser

from threading import Thread, Lock
from struct import unpack

import trdTablemodel
import util

from trdmasterui import Ui_MainWindow
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class uicontrol(QMainWindow, Ui_MainWindow):
    def __init__(self, ptfmodel):
        QMainWindow.__init__(self)
        self.ptfmodel = ptfmodel

    def setup(self):
        self.setupUi(self)
        self.tableView.setModel(self.ptfmodel)

        self.on_ontopchk_stateChanged(self.ontopchk.checkState())

    @pyqtSlot(int)
    def on_ontopchk_stateChanged(self, state):
        flags = self.windowFlags()
        if self.ontopchk.isChecked():
            self.setWindowFlags(flags|Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags^(Qt.WindowStaysOnTopHint));
        self.show()

class masterHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        while 1:
            try:
                (msglen,) = unpack("!I", self.rfile.read(4))
                cmd = pickle.loads(self.rfile.read(msglen))
            except socket.error:
                break

            handler = None
            try:
                handler = getattr(self, cmd.cmdname+"Handler")
            except AttributeError:
                #print("unknown cmd: <%s>" % str(cmd))
                self.server.logger.exception("unknown cmd: <%s>", str(cmd))

            try:
                if handler:
                    self.server.logger.info("caling handler: %s",
                            cmd.cmdname+"Handler")
                    handler(*cmd.args, **cmd.kwargs)
            except:
                self.server.logger.exception("handler meets exception.")

    def registerHandler(self, *args, **kwargs):
        """
        register
        [username, ptfname]
        {}
        """
        try:
            pass
            #s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #s.connect( (args[2],args[3]) )
        except socket.error:
            self.logger.exception("cannot connect back to client.")
            #print("cannot connect back to client.")

        with self.server.lock:
            self.server.csockmap[args[0]][args[1]] = self.request
            self.server.ptfmodel.beginInsertRows(QModelIndex(), 0, 0)
            self.server.ptfdata.addrow(args[1])
            self.server.ptfmodel.endInsertRows()
            self.server.ptfdata.data[args[1]]["username"] = args[0]
            self.server.ptfdata.data[args[1]]["ptfname"] = args[1]

    def pstatreportHandler(self, *args, **kwargs):
        if args[0] in self.server.ptfdata.data:
            self.server.ptfdata.data[args[0]].update(kwargs)
            QMetaObject.invokeMethod(self.server.ptfmodel, "updaterow",
                    Qt.QueuedConnection,
                    Q_ARG("int",
                        self.server.ptfmodel.rownum(args[0])))
        else:
            self.logger.info("pstat from unknown source: %s", args[0])

class masterServer(SocketServer.ThreadingTCPServer):
    def __init__(self, server_addr, RequestHandlerClass,
            csockmap, ptfmodel, ptfdata):
        """
        assumption: masterServer should NOT send data to clients.
                the message is sent by a separated thread,
                and it is triggered by UI, timers, or so.
        """

        SocketServer.ThreadingTCPServer.__init__(self,
                server_addr, RequestHandlerClass)

        self.csockmap = csockmap
        self.ptfmodel = ptfmodel
        self.ptfdata = ptfdata
        self.lock = Lock()
        self.logger = logging.getLogger()

def main(args):
    # data structures:
    # user, ptf -> socket

    app = QApplication(args)
    os.chdir(os.path.dirname(os.path.abspath(args[0])))

    CONFIGFN = "trdmaster.cfg"
    try:
        CONFIGFN = sys.argv[1]
    except IndexError:
        pass
    LOGDIR = "log"
    if not os.path.isdir(LOGDIR):
        try:
            os.mkdir(LOGDIR)
        except OSError as e:
            print "cannot make log directory: %d, %s." % (e.errno, e.strerror)
            QMessageBox.information(None, "", u"不能创建log目录: %d, %s" % (e.errno, e.strerror))
            sys.exit(1)

    config = ConfigParser.RawConfigParser()
    config.read(CONFIGFN)

    MYSEC = "master"

    # setup logging
    logging.config.fileConfig(CONFIGFN)
    logger = logging.getLogger()
    msg = "i'm started"
    logger.info("========================")
    logger.info(msg)

    # init datas
    csockmap = util.dictdict()
    ptfdata = trdTablemodel.trdData()
    ptfdata.colname = ["username", "ptfname", "buytotalw", "stopped"]
    ptfmodel = trdTablemodel.TradeTableModel_dd(ptfdata)

    # setup ui
    uic = uicontrol(ptfmodel)
    uic.setup()

    # start master socket server
    mserver = masterServer( ("127.0.0.1", config.getint(MYSEC, "port")),
            masterHandler,
            csockmap, ptfmodel, ptfdata)
    t = Thread(target=mserver.serve_forever)
    t.start()

    uic.show()
    app.exec_()

    # exit process
    mserver.shutdown()
    t.join()

if __name__=="__main__":
    main(sys.argv)
