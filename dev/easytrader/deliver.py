# -*- coding: utf-8 -*-

import os
import sys
import time
import random
import datetime
from threading import Thread
import ConfigParser

from dbfpy import dbf
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.phonon import *

import jsd
from deliverdlg import Ui_deliverdlg
from easytrader_lib import calsicontracts

class deliverdlg(QDialog, Ui_deliverdlg):
    def __init__(self):
        QDialog.__init__(self)

    def setup(self):
        self.setupUi(self)

        #s = jsd.session(jsdcfg)
        #if not s.setup():
        #    pass

    @pyqtSlot(QString)
    def fillcombo(self, item):
        self.sindexcmb.addItem(item)

class updater(Thread):
    def __init__(self, ui, config):
        Thread.__init__(self)
        self.ui = ui
        self.config = config
        self.runflag = True

        self.hs300index = ""
        self.dbsh = None
        self.jsdsession = None

        self.sindexlist = calsicontracts()

        self.m_media = Phonon.MediaObject(self.ui)
        audioOutput = Phonon.AudioOutput(Phonon.MusicCategory,
                self.ui)
        Phonon.createPath(self.m_media, audioOutput)
        self.playsignal = self.ui.playsignalchk.isChecked()
        self.ui.connect(self.ui.playsignalchk, SIGNAL("stateChanged(int)"), self.setplay)
        self.ui.connect(self.m_media, SIGNAL("aboutToFinish()"), self.addsong)

        musicdir = u"music"
        self.musicdir = musicdir
        self.musicfn = random.choice(os.listdir(musicdir))
        self.m_media.setCurrentSource(Phonon.MediaSource(os.path.join(musicdir,
            self.musicfn)))

    def setnotice(self, msg):
        QMetaObject.invokeMethod(self.ui.statusline, "setText",
                Qt.QueuedConnection,
                Q_ARG("QString", QString(msg)))

    def setup(self):
        dbfn = self.config.get("deliver", "dbfn")
        dbsh = dbf.Dbf(dbfn, ignoreErrors=True, readOnly=True)
        i = 0
        hs300index = -1
        hs300code = "000300"
        for rec in dbsh:
            if rec["S1"] == hs300code:
                hs300index = i
                break
            i = i + 1
        if hs300index == -1:
            self.setnotice(u"读股票行情错误：沪深300索引未找到")
            return False

        self.hs300index = hs300index
        self.dbsh = dbsh

        JSDSEC = "jsd"
        jsdcfg = {}
        for k,v in self.config.items(JSDSEC):
            jsdcfg[k] = v
        try:
            jsdcfg["jsdport"] = int(jsdcfg["jsdport"])
        except KeyError:
            pass
        
        s = jsd.session(jsdcfg)
        if not s.setup():
            self.setnotice(u"不能连接金士达")
            s.close()
            return False
        self.jsdsession = s

        for sindex in self.sindexlist:
            QMetaObject.invokeMethod(self.ui, "fillcombo",
                    Qt.QueuedConnection,
                    Q_ARG("QString", QString(sindex)))

        return True

    def run(self):
        if not self.setup():
            return

        START = datetime.time(13, 00, 00)
        END = datetime.time(15, 00, 00)

        now = datetime.datetime.now().time()

        if now < START:
            self.setnotice(u"等待开始计算时间：%s" % str(START))

            while 1 and self.runflag:
                time.sleep(1)
                now = datetime.datetime.now().time()
                if now >= START:
                    break

        if not self.runflag:
            return

        avg = 0
        n = 0
        self.setnotice(u"正在计算收割价格")
        while self.runflag:
            now = datetime.datetime.now().time()
            if now > END:
                self.setnotice(u"计算完成")
                break

            # delivery price
            a = self.dbsh[self.hs300index]["S8"]
            avg = avg * n / (n+1) + a / (n+1)
            n = n + 1
            QMetaObject.invokeMethod(self.ui.hs300avgline,
                    "setText",
                    Qt.QueuedConnection,
                    Q_ARG("QString", QString("%0.3f"%avg)))

            # stock index price
            hqreq = jsd.QueryHQReq(self.jsdsession)
            hqreq["exchcode"] = self.jsdsession["cffexcode"]
            hqreq["code"] = self.sindexlist[self.ui.sindexcmb.currentIndex()]
            hqreq.send()
            hqresp = jsd.QueryHQResp(self.jsdsession)
            hqresp.recv()
            if hqresp.anwser == "N":
                continue
            silatest = float(hqresp.records[0][9])
            QMetaObject.invokeMethod(self.ui.sindexline,
                    "setText",
                    Qt.QueuedConnection,
                    Q_ARG("QString", QString("%0.3f"%silatest)))

            # the price diff
            diff = silatest - avg
            QMetaObject.invokeMethod(self.ui.diffline,
                    "setText",
                    Qt.QueuedConnection,
                    Q_ARG("QString", QString("%0.3f"%diff)))
            diffper = diff / avg * 100
            QMetaObject.invokeMethod(self.ui.diffperline,
                    "setText",
                    Qt.QueuedConnection,
                    Q_ARG("QString", QString("%0.2f %%"%diffper)))
            warnthreshold = self.ui.warnspin.value()
            if diffper >= warnthreshold or -diffper <= warnthreshold:
                self.play()
            else:
                self.stopplay()
            time.sleep(1)

        #QMetaObject.invokeMethod(self.ui, "fullcombo",
        #        Qt.QueuedConnection)

    def stop(self):
        self.runflag = False

    @pyqtSlot(int)
    def setplay(self, state):
        self.playsignal = self.ui.playsignalchk.isChecked()
        if not self.playsignal:
            self.stopplay()

    @pyqtSlot()
    def addsong(self):
        self.musicfn = random.choice(os.listdir(self.musicdir))
        self.m_media.enqueue(Phonon.MediaSource(os.path.join(self.musicdir, self.musicfn)))

    @pyqtSlot()
    def play(self):
        if self.playsignal:
            self.m_media.play()

    @pyqtSlot()
    def stopplay(self):
        self.m_media.pause()

def main(args):
    app = QApplication(args)
    ddlg = deliverdlg()
    ddlg.setup()

    cfgfn = "deliver.cfg"
    try:
        cfgfn = sys.argv[1]
    except IndexError:
        pass

    config = ConfigParser.RawConfigParser()
    config.read(cfgfn)

    u = updater(ddlg, config)
    u.start()

    ddlg.show()
    app.exec_()

    u.stop()
    u.join()

if __name__=="__main__":
    main(sys.argv)
