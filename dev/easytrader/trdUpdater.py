from threading import Thread
import logging
import pickle, zlib

import util

class metaUpdater(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.runflag = True
        self.logger = logging.getLogger()
        self.name = self.__class__.__name__

    def setup(self):
        pass

    def update(self):
        pass

    def close(self):
        pass

    def stop(self):
        self.runflag = False

    def run(self):
        try:
            try:
                ret = self.setup()
                if not ret:
                    self.logger.error("setup failed")
                    return
            except Exception:
                self.logger.exception("setup failed")
                return


            while self.runflag:
                self.update()

            self.close()
        except Exception:
            self.logger.exception("OMG, updater meets unhandled exception.")

class SIFQuoteUpdater_net(metaUpdater):
    def __init__(self, servhost, servport):
        metaUpdater.__init__(self)
        self.servhost = servhost
        self.servport = servport
        self.conn = None

    def setup(self):
        try:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.connect((self.servhost, self.servport))
        except socket.error:
            self.logger.exception("cannot connect to quoteserver")
            return False

    def stop(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def update(self):
        (pktlen,) = unpack("!I", util.recv_n(self.conn, 4))

        data = util.recv_n(self.conn, pktlen)
        data = pickle.loads(zlib.decompress(data))

        self.on_quoteupdate(data)

    def on_quoteupdate(data):
        pass

