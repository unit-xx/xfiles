import sys
import socket
import pickle
import SocketServer

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
            handler = getattr(self.server, cmd.cmdname+"Handler")
            return handler(*cmd.args, **cmd.kwargs)
        except AttributeError:
            print("unknown cmd: <%s>" % str(cmd))
            #self.logger.warning("unknown cmd: <%s>", str(cmd))


class masterServer(SocketServer.ThreadingTCPServer):
    def __init__(self, server_addr, RequestHandlerClass,
            csockmap, ptfmodel, ptfdata):
        """
        assumption: masterServer should not send data to clients.
                the message is sent by main thread, and it is triggered
                by UI, or timers.
        """

        SocketServer.ThreadingTCPServer.__init__(self,
                server_addr, RequestHandlerClass)

        self.csockmap = csockmap
        self.ptfmodel = ptfmodel
        self.ptfdata = ptfdata

    def registerHandler(self, *args, **kwargs):
        """
        register
        [username, ptfname, ip, port]
        {}
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect( (args[2],args[3]) )
        except socket.error:
            #self.logger.expection("cannot connect back to client.")
            print("cannot connect back to client.")

        self.csockmap[args[0]][args[1]] = s
        self.ptfmodel.beginInsertRows(QModelIndex(), 0, 0)
        self.ptfdata.addrow(args[1])
        self.ptfmodel.endInsertRows()
        self.ptfdata.data[args[1]]["username"] = args[0]
        self.ptfdata.data[args[1]]["ptfname"] = args[1]


def main(args):
    # data structures:
    # user, ptf -> socket

    app = QApplication(args)
    # init datas
    csockmap = util.dictdict()
    ptfdata = trdTablemodel.trdData()
    ptfdata.colname = ["username", "ptfname"]
    ptfmodel = trdTablemodel.TradeTableModel_dd(ptfdata)

    # setup ui
    uic = uicontrol(ptfmodel)
    uic.setup()

    # start master socket server
    mserver = masterServer( ("127.0.0.1", 38888),
            masterHandler,
            csockmap, ptfmodel, ptfdata)
    t = Thread(target=mserver.serve_forever)
    t.start()

    uic.show()
    app.exec_()

    # exit process
    t.join()

if __name__=="__main__":
    main(sys.argv)
