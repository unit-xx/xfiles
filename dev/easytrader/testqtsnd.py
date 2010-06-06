# -*- coding: utf-8 -*-
import os
import sys

from PyQt4.QtGui import QApplication, QMainWindow, QDirModel, QColumnView
from PyQt4.QtGui import QFrame
from PyQt4.QtCore import SIGNAL
from PyQt4.phonon import Phonon

def main():
    app = QApplication(sys.argv)
    #QApplication.setApplicationName("Phonon Tutorial 2 (Python)")
    #mw = MainWindow()
    #mw.show()
    #sys.exit(app.exec_())

    m_media = Phonon.MediaObject()
    audioOutput = Phonon.AudioOutput(Phonon.MusicCategory)
    Phonon.createPath(m_media, audioOutput)

    m_media.setCurrentSource(Phonon.MediaSource("h:\\music\\Sarah.Brightman.-.[The.Andrew.Lloyd.Webber.Collection].专辑.(APE).ape"))
    m_media.play()
    app.exec_()

if __name__ == '__main__':
    main()

