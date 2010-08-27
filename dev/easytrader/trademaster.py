# -*- coding: utf-8 -*-

import sys, os
import logging
import logging.config
import socket
import pickle
import SocketServer
import ConfigParser

from threading import Thread
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

class masterHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        (msglen,) = unpack("!I", self.rfile.read(4))
        cmd = pickle.loads(self.rfile.read(msglen))
        try:
            handler = getattr(self, cmd.cmdname+"Handler")
            return handler(*cmd.args, **cmd.kwargs)
        except AttributeError:
            #print("unknown cmd: <%s>" % str(cmd))
            self.server.logger.exception("unknown cmd: <%s>", str(cmd))

    def registerHandler(self, *args, **kwargs):
        """
        register
        [username, ptfname, ip, port]
        {}
        """
        try:
            pass
            #s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #s.connect( (args[2],args[3]) )
        except socket.error:
            self.logger.exception("cannot connect back to client.")
            #print("cannot connect back to client.")

        self.server.csockmap[args[0]][args[1]] = self.request
        self.server.ptfmodel.beginInsertRows(QModelIndex(), 0, 0)
        self.server.ptfdata.addrow(args[1])
        self.server.ptfmodel.endInsertRows()
        self.server.ptfdata.data[args[1]]["username"] = args[0]
        self.server.ptfdata.data[args[1]]["ptfname"] = args[1]

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
    ptfdata.colname = ["username", "ptfname"]
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
