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
    def __init__(self, ptfmodel, mserver):
        QMainWindow.__init__(self)
        self.ptfmodel = ptfmodel
        self.mserver = mserver

    def setup(self):
        self.setupUi(self)
        self.tableView.setModel(self.ptfmodel)
        self.ptfmodel.table = self.tableView

        self.on_ontopchk_stateChanged(self.ontopchk.checkState())
        self.on_lockchk_stateChanged(self.lockchk.checkState())

        # fill stock price combos
        self.pricepolicylist = ["latest", "s5", "s4", "s3", "s2", "s1", "b1", "b2", "b3", "b4", "b5"]
        self.sindexpricepolicylist = ["mktval", "latest", "s1", "b1", ]
        self.buypolicy = "latest"
        self.sellpolicy = "latest"
        self.openpolicy = "mktval"
        self.closepolicy = "mktval"
        self.pricepolicynamemap = {"latest":u"最新价",
                "s5":u"卖五",
                "s4":u"卖四",
                "s3":u"卖三",
                "s2":u"卖二",
                "s1":u"卖一",
                "b1":u"买一",
                "b2":u"买二",
                "b3":u"买三",
                "b4":u"买四",
                "b5":u"买五",
                "mktval":u"市价"
                }

        for price in self.pricepolicylist:
            self.pricepolicybuy.addItem(self.pricepolicynamemap[price])
            self.pricepolicysell.addItem(self.pricepolicynamemap[price])
        self.pricepolicybuy.setCurrentIndex(self.pricepolicylist.index(self.buypolicy))
        self.pricepolicysell.setCurrentIndex(self.pricepolicylist.index(self.sellpolicy))

        for price in self.sindexpricepolicylist:
            self.openpricecmbox.addItem(self.pricepolicynamemap[price])
            self.closepricecmbox.addItem(self.pricepolicynamemap[price])
        self.openpricecmbox.setCurrentIndex(self.sindexpricepolicylist.index(self.openpolicy))
        self.closepricecmbox.setCurrentIndex(self.sindexpricepolicylist.index(self.closepolicy))

    def getselected(self):
        ptfindex = []
        sel = self.tableView.selectionModel().selectedRows()
        for s in sel:
            ptfindex.append(self.mserver.ptfdata.getrow(s.row()))
        return ptfindex

    @pyqtSlot(int)
    def on_ontopchk_stateChanged(self, state):
        flags = self.windowFlags()
        if self.ontopchk.isChecked():
            self.setWindowFlags(flags|Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags^(Qt.WindowStaysOnTopHint));
        self.show()

    @pyqtSlot()
    def on_raisebtn_clicked(self):
        self.sendraise()

    def sendraise(self):
        ptfs = self.getselected()
        for p in ptfs:
            s = self.mserver.csockmap[p]
            cmd = util.command()
            cmd.cmdname = "raise"
            s.sendall(cmd.pack())


    def sendbutton(self):
        ptfs = self.getselected()
        for p in ptfs:
            s = self.mserver.csockmap[p]
            btnname = str(self.sender().objectName())
            cmd = util.command()
            cmd.cmdname = "button"
            cmd.args.append(btnname)
            s.sendall(cmd.pack())

    def sendcheckbox(self):
        ptfs = self.getselected()
        for p in ptfs:
            s = self.mserver.csockmap[p]
            chkname = str(self.sender().objectName())
            cmd = util.command()
            cmd.cmdname = "checkbox"
            cmd.args.append(chkname)
            cmd.args.append(self.sender().isChecked())
            s.sendall(cmd.pack())

    def senddoublespin(self, value):
        ptfs = self.getselected()
        for p in ptfs:
            s = self.mserver.csockmap[p]
            spinname = str(self.sender().objectName())
            cmd = util.command()
            cmd.cmdname = "doublespin"
            cmd.args.append(spinname)
            cmd.args.append(value)
            s.sendall(cmd.pack())

    def sendcombo(self, index):
        ptfs = self.getselected()
        for p in ptfs:
            s = self.mserver.csockmap[p]
            comboname = str(self.sender().objectName())
            cmd = util.command()
            cmd.cmdname = "combo"
            cmd.args.append(comboname)
            cmd.args.append(index)
            s.sendall(cmd.pack())

    @pyqtSlot()
    def on_selall_clicked(self):
        self.tableView.selectAll()
    
    @pyqtSlot()
    def on_deselall_clicked(self):
        self.tableView.clearSelection()

    @pyqtSlot(int)
    def on_lockchk_stateChanged(self, state):
        self.ctltab.setEnabled(not self.lockchk.isChecked())

    # buttons
    @pyqtSlot()
    def on_buyorder_clicked(self):
        ret = True
        if self.confirmchk.isChecked():
            ret = QMessageBox.warning(self,
                    u"",
                    u"<H3>确认买入？</H3>",
                    QMessageBox.Ok|QMessageBox.Cancel)
        if ret:
            self.sendbutton()

    @pyqtSlot()
    def on_buyorderbatch_clicked(self):
        ret = True
        if self.confirmchk.isChecked():
            ret = QMessageBox.warning(self,
                    u"",
                    u"<H3>确认买入？</H3>",
                    QMessageBox.Ok|QMessageBox.Cancel)
        if ret:
            self.sendbutton()

    @pyqtSlot()
    def on_cancelbuyorder_clicked(self):
        self.sendbutton()

    @pyqtSlot()
    def on_saveorder_2_clicked(self):
        self.sendbutton()

    @pyqtSlot()
    def on_opensifbtn_clicked(self):
        ret = True
        if self.confirmchk.isChecked():
            ret = QMessageBox.warning(self,
                    u"",
                    u"<H3>确认卖空？</H3>",
                    QMessageBox.Ok|QMessageBox.Cancel)
        if ret:
            self.sendbutton()

    @pyqtSlot()
    def on_cancelopensifbtn_clicked(self):
        self.sendbutton()

    @pyqtSlot()
    def on_sellorder_clicked(self):
        ret = True
        if self.confirmchk.isChecked():
            ret = QMessageBox.warning(self,
                    u"",
                    u"<H3>确认卖出？</H3>",
                    QMessageBox.Ok|QMessageBox.Cancel)
        if ret:
            self.sendbutton()

    @pyqtSlot()
    def on_sellorderbatch_clicked(self):
        ret = True
        if self.confirmchk.isChecked():
            ret = QMessageBox.warning(self,
                    u"",
                    u"<H3>确认卖出？</H3>",
                    QMessageBox.Ok|QMessageBox.Cancel)
        if ret:
            self.sendbutton()

    @pyqtSlot()
    def on_cancelsellorder_clicked(self):
        self.sendbutton()

    @pyqtSlot()
    def on_saveorder_clicked(self):
        self.sendbutton()

    @pyqtSlot()
    def on_closesifbtn_clicked(self):
        ret = True
        if self.confirmchk.isChecked():
            ret = QMessageBox.warning(self,
                    u"",
                    u"<H3>确认空平？</H3>",
                    QMessageBox.Ok|QMessageBox.Cancel)
        if ret:
            self.sendbutton()

    @pyqtSlot()
    def on_cancelclosesifbtn_clicked(self):
        self.sendbutton()

    # combos
    @pyqtSlot(int)
    def on_pricepolicybuy_currentIndexChanged(self, index):
        self.sendcombo(index)

    @pyqtSlot(int)
    def on_openpricecmbox_currentIndexChanged(self, index):
        self.sendcombo(index)

    @pyqtSlot(int)
    def on_pricepolicysell_currentIndexChanged(self, index):
        self.sendcombo(index)

    @pyqtSlot(int)
    def on_closepricecmbox_currentIndexChanged(self, index):
        self.sendcombo(index)

    # checkboxes
    @pyqtSlot(int)
    def on_forcecancelbuychk_stateChanged(self, state):
        self.sendcheckbox()

    @pyqtSlot(int)
    def on_forcecancelsellchk_stateChanged(self, state):
        self.sendcheckbox()

    # spins
    @pyqtSlot(float)
    def on_buypricefixspin_valueChanged(self, value):
        self.senddoublespin(value)

    @pyqtSlot(float)
    def on_openpricefixspin_valueChanged(self, value):
        self.senddoublespin(value)

    @pyqtSlot(float)
    def on_sellpricefixspin_valueChanged(self, value):
        self.senddoublespin(value)

    @pyqtSlot(float)
    def on_closepricefixspin_valueChanged(self, value):
        self.senddoublespin(value)


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
                self.server.logger.exception("unknown cmd: <%s>", str(cmd))

            try:
                if handler:
                    shouldexit = handler(*cmd.args, **cmd.kwargs)
                    if shouldexit == True:
                        break
            except:
                self.server.logger.exception("handler meets exception.")

    def registerHandler(self, *args, **kwargs):
        """
        register
        [username, ptfname]
        {}
        """
        with self.server.lock:
            if args[1] not in self.server.ptfdata:
                self.server.csockmap[args[1]] = self.request
                self.server.ptfmodel.beginInsertRows(QModelIndex(), 0, 0)
                self.server.ptfdata.addrow(args[1])
                self.server.ptfmodel.endInsertRows()
                self.server.ptfdata.data[args[1]]["username"] = args[0]
                self.server.ptfdata.data[args[1]]["ptfname"] = args[1]
                if len(self.server.ptfdata) == 1:
                    self.server.ptfmodel.table.resizeColumnsToContents()
            else:
                self.server.logger.warning("duplicated register")
                return True
        return False

    def unregisterHandler(self, *args, **kwargs):
        """
        unregister
        [username, ptfname]
        {}
        """
        with self.server.lock:
            if args[1] in self.server.ptfdata:
                self.server.csockmap[args[1]] = None
                r = self.server.ptfmodel.rownum(args[1])
                self.server.ptfmodel.beginRemoveRows(QModelIndex(), r, r)
                self.server.ptfdata.delrow(r)
                self.server.ptfmodel.endRemoveRows()
        return True

    def pstatreportHandler(self, *args, **kwargs):
        """
        pstatreport
        [ptfname]
        {<data>}
        """
        if args[0] in self.server.ptfdata.data:
            self.server.ptfdata.data[args[0]].update(kwargs)
            QMetaObject.invokeMethod(self.server.ptfmodel, "updaterow",
                    Qt.QueuedConnection,
                    Q_ARG("int",
                        self.server.ptfmodel.rownum(args[0])))
        else:
            self.logger.info("pstat from unknown source: %s", args[0])
        return False

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
    csockmap = dict()
    ptfdata = trdTablemodel.trdData()
    ptfdata.colname = ["username", "ptfname",
            "basediff", "basediffper",
            "shares", "openshares", "closeshares", "state",
            "buytotalw", "buypoint", "selltotalw", "sellpoint",
            "stopped",
            "buyable", "buycomplete", "sellable", "sellcomplete"]
    ptfdata.colnamemap = {
            "username":u"用户",
            "ptfname":u"组合", 
            "basediff":u"基差",
            "basediffper":u"基差%",
            "shares":u"期货手数",
            "openshares":u"开仓手数",
            "closeshares":u"平仓手数",
            "state":u"状态",
            "buytotalw":u"买入（万）",
            "buypoint":u"买入点",
            "selltotalw":u"卖出（万）",
            "sellpoint":u"卖出点",
            "stopped":u"停牌",
            "buyable":u"可买",
            "buycomplete":u"已买入",
            "sellable":u"可卖",
            "sellcomplete":u"已卖出",
            }
    ptfmodel = trdTablemodel.TradeTableModel_dd(ptfdata)

    # start master socket server
    mserver = masterServer( ("", config.getint(MYSEC, "port")),
            masterHandler,
            csockmap, ptfmodel, ptfdata)
    t = Thread(target=mserver.serve_forever)
    t.start()

    # setup ui
    uic = uicontrol(ptfmodel, mserver)
    uic.setup()

    uic.show()
    app.exec_()

    # exit process
    mserver.shutdown()
    t.join()

if __name__=="__main__":
    main(sys.argv)
