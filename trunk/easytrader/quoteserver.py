import os
import sys
import time
import socket
import logging
import logging.config
import SocketServer
from threading import Thread, Lock
import ConfigParser

class QuoteReqHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        # add the connection to a queue
        logger = logging.getLogger()
        logger.info("pushee to be added: %s", self.request.getpeername())
        self.server.pset.add(self.request)

class QuotePusher(Thread):
    def __init__(self, pset):
        Thread.__init__(self)
        self.name = "QuotePusher"
        self.logger = logging.getLogger()
        self.pset = pset
        self.runflag = True

    def run(self):
        """
        read quote info and push it to a list of connections
        """
        while self.runflag:
            quote = "if xxx"
            self.pset.broadcast(quote)
            time.sleep(1)
        self.pset.closeall()

    def stop(self):
        self.runflag = False
            

class QuotePusheeSet:
    def __init__(self):
        self.pushee = set()
        self.plock = Lock()
        self.logger = logging.getLogger()

    def add(self, p):
        with self.plock:
            self.pushee.add(p)

    def remove(self):
        pass

    def closeall(self):
        with self.plock:
            for p in self.pushee:
                try:
                    p.close()
                except socket.error:
                    pass

    def broadcast(self, msg):
        with self.plock:
            toremove = set()
            for p in self.pushee:
                try:
                    p.sendall(msg)
                except socket.error:#pushee connection may close
                    toremove.add(p)
            if len(toremove) > 0:
                for p in toremove:
                    self.logger.info("pushee to be removed: %s", p.getpeername())
                self.pushee -= toremove


class QuoteServer(SocketServer.ThreadingTCPServer):
    def __init__(self, server_address, RequestHandlerClass):
        """
        init and make a new QuotePusheeSet object
        start a QuotePusher
        """
        SocketServer.ThreadingTCPServer.__init__(self, server_address, RequestHandlerClass)
        self.pset = QuotePusheeSet()
        self.pusher = QuotePusher(self.pset)
        self.pusher.start()

    def close_request(self, request):
        """
        intentially leave the function empty, so that the requsts are not
        close after processed by QuoteReqHandler.
        """
        pass

    def stoppusher(self):
        self.pusher.stop()
        self.pusher.join()

def main(args):

    os.chdir(os.path.dirname(os.path.abspath(args[0])))
    # make log directory
    LOGDIR = "log"
    if not os.path.isdir(LOGDIR):
        try:
            os.mkdir(LOGDIR)
        except OSError as e:
            print "cannot make log directory: %d, %s." % (e.errno, e.strerror)
            sys.exit(1)

    CONFIGFN = "quoteserver.cfg"
    logging.config.fileConfig(CONFIGFN)
    logger = logging.getLogger()
    msg = "i'm started"
    logger.info("========================")
    logger.info(msg)

    config = ConfigParser.RawConfigParser()
    config.read(CONFIGFN)
    MYSEC = "quoteserver"
    PORT = config.getint(MYSEC, "port")
    HOST = ""

    server = QuoteServer((HOST, PORT), QuoteReqHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.stoppusher()

if __name__=="__main__":
    main(sys.argv)

