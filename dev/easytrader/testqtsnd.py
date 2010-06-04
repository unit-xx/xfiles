from PyQt4.phonon import Phonon

        #self.m_media.setCurrentSource(self.m_model.filePath(index))
        self.m_media.setCurrentSource(
            Phonon.MediaSource(self.m_model.filePath(index)))
        self.m_media.play()

    def delayedInit(self):
        if not self.m_media:

m_media = Phonon.MediaObject(
audioOutput = Phonon.AudioOutput(Phonon.MusicCategory, self)
Phonon.createPath(self.m_media, audioOutput)

