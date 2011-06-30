import os
import sys
import time
import socket
import logging
import logging.config
import SocketServer
import ConfigParser
from threading import Thread, Lock
from struct import pack, unpack

class QuoteReqHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        # add the connection to a queue
        logger = logging.getLogger()
        pname = self.request.getpeername()
        logger.info("pushee to be added: %s", pname)
        self.server.pset.add(self.request)
        logger.info("pushee already added: %s", pname)

class QuotePusher(Thread):
    def __init__(self, pset, param):
        Thread.__init__(self)
        self.name = "QuotePusher"
        self.logger = logging.getLogger()
        self.pset = pset
        self.param = param
        self.runflag = True

    def run(self):
        """
        read quote info and push it to a list of connections
        """
        try:
            self.setup(self.param)
        except Exception:
            self.logger.exception("QuotePusher setup failed")
            return

        while self.runflag:
            try:
                quote = self.updatequote()
                if quote is not None:
                    self.pset.broadcast(quote)
            except:
                self.logger.exception("Exception while updating quote.")
                self.runflag = False

        self.finalize()
        self.pset.closeall()

    def updatequote(self):
        time.sleep(1)
        return "no quote"

    def setup(self, param):
        pass

    def finalize(self):
        pass

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

    def size(self):
        return len(self.pushee)

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
                    p.sendall(pack("!I", len(msg)))
                    p.sendall(msg)
                except socket.error, e:#pushee connection may close
                    toremove.add(p)
            if len(toremove) > 0:
                self.logger.info("pushee to be removed: %s", "|".join([str(x.getpeername()) for x in toremove]))
                self.pushee -= toremove
                self.logger.info("pushee still in queue: %s", "|".join([str(x.getpeername()) for x in self.pushee]))

class QuoteServer(SocketServer.ThreadingTCPServer):
    def __init__(self, server_address, RequestHandlerClass, QuotePusherClass, param):
        """
        init and make a new QuotePusheeSet object
        start a QuotePusher
        """
        SocketServer.ThreadingTCPServer.__init__(self, server_address, RequestHandlerClass)
        self.pset = QuotePusheeSet()
        self.pusher = QuotePusherClass(self.pset, param)
        self.pusher.start()

    def shutdown_request(self, request):
        """
        intentially leave the function empty, so that the requsts are not
        close after processed by QuoteReqHandler.

        shutdown_request is new in Python 2.7, which almost replace/wrap close_request.
        """
        pass

    def close_request(self, request):
        """
        intentially leave the function empty, so that the requsts are not
        close after processed by QuoteReqHandler.
        """
        pass

    def stoppusher(self):
        self.pusher.stop()
        self.pusher.join()

def startserver(configfn, QuotePusherClass, param = {}, QuoteServerClass=QuoteServer):

    os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
    # make log directory
    LOGDIR = "log"
    if not os.path.isdir(LOGDIR):
        try:
            os.mkdir(LOGDIR)
        except OSError as e:
            print "cannot make log directory: %d, %s." % (e.errno, e.strerror)
            sys.exit(1)

    logging.config.fileConfig(configfn)
    logger = logging.getLogger()
    msg = "i'm started"
    logger.info("========================")
    logger.info(msg)

    config = ConfigParser.RawConfigParser()
    config.read(configfn)
    MYSEC = "quoteserver"
    MYPORT = "port"
    MYHOST = "host"
    PORT = config.getint(MYSEC, MYPORT)
    HOST = config.get(MYSEC, MYHOST)

    server = QuoteServerClass((HOST, PORT), QuoteReqHandler, QuotePusherClass, param)
    try:
        server.serve_forever()
    except KeyboardInterrupt, Exception:
        logger.warning("Server stopped by exception.")
    server.stoppusher()

if __name__=="__main__":
    configfn = "quoteserver.cfg"
    startserver(configfn, QuotePusher)

