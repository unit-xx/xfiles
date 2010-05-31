import socket
import SocketServer
from threading import Thread, Lock

class QuoteReqHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        # add the connection to a queue
        pass

class QuotePusher(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        """
        read quote info and push it to a list of connections
        """

class QuotePushee:
    def __init__(self):
        self.pushee = []
        self.plock = Lock()

    def add(self):
        pass

    def remove(self):
        pass

class QuoteServer(SocketServer.ThreadingTCPServer):
    def __init__(self):
        """
        init and make a new QuotePushee object
        start a QuotePusher
        """
        pass

if __name__=="__main__":
    HOST, PORT = "localhost", 20888

    server = QuoteServer((HOST, PORT), QuoteReqHandler)
    server.server_forever()
