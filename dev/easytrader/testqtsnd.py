# -*- coding: utf-8 -*-

import sys

from PyQt4.QtGui import QApplication, QMainWindow, QDirModel, QColumnView
from PyQt4.QtGui import QFrame
from PyQt4.QtCore import *
from PyQt4.phonon import Phonon

class MainWindow(QMainWindow):

    m_model = QDirModel()

    def __init__(self):
        QMainWindow.__init__(self)
        self.m_fileView = QColumnView(self)
        self.m_media = None

        self.setCentralWidget(self.m_fileView)
        self.m_fileView.setModel(self.m_model)
        self.m_fileView.setFrameStyle(QFrame.NoFrame)

        self.connect(self.m_fileView,
            SIGNAL("updatePreviewWidget(const QModelIndex &)"), self.play)

        cl = Phonon.BackendCapabilities.availableMimeTypes()
        for c in cl:
            print c
        
    @pyqtSlot(long)
    def showtick(self, t):
        print t

    def play(self, index):
        self.delayedInit()
        #self.m_media.setCurrentSource(self.m_model.filePath(index))
        self.m_media.setCurrentSource(
            Phonon.MediaSource(self.m_model.filePath(index)))
        self.m_media.play()

    def delayedInit(self):
        if not self.m_media:
            self.m_media = Phonon.MediaObject(self)
            audioOutput = Phonon.AudioOutput(Phonon.MusicCategory, self)
            Phonon.createPath(self.m_media, audioOutput)
            self.m_media.setTickInterval(1000)
            print self.connect(self.m_media, SIGNAL("tick(qint64)"), self.showtick)

def main():
    app = QApplication(sys.argv)
    QApplication.setApplicationName("Phonon Tutorial 2 (Python)")
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
