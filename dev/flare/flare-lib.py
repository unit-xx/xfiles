import sys
import logging
import Queue
from threading import Thread, currentThread, Lock, Event
import UUID

class qserver:
    '''
    receiving quotation from ctp and store it in redis or memory
    '''
    def __init__(self, qsconfig):
        self.serv = qsconfig.serv

    def quote(inst):
        pass

class engine:
    def __init__(self, tcap=10):
        self.tqueue = Queue.Queue()
        self.tcap = tcap
        self.tpool = []

    def setup(self):
        # start thread pool
        pass

    def addtask(self, t):
        self.tqueue.put(t)

class engine_worker(Thread):
    def __init__(self, tqueue, qserv):
        Thread.__init__(self)
        self.tqueue = tqueue
        self.qserv = qserv
        self.name = self.__class__.__name__
        self.logger = logging.getLogger()
        self.runflag = True

    def setup(self):
        return True

    def close(self):
        pass

    def run(self):
        try:
            if not self.setup():
                self.logger.warning("setup failed")
                self.close()
                return

            self.logger.info("setup ok.")
            while self.runflag:
                try:
                    t = self.tqueue.get(True, 2)
                    try:
                        self.dotask(t)
                    except Exception:
                        self.logger.exception("dotask exception.")
                    self.dbqueue.task_done()
                except Queue.Empty:
                    pass
            self.close()

        except Exception:
            self.close()
            self.logger.exception("dbserver exit exceptionally.")

    def dotask(self, task):
        pass

    def stop(self):
        self.runflag = False

class orderman:
    '''
    1. provide interface for order read/write
    2. order recovery on startup
    '''
    def __init__(self):
        self.ref2ordmap = {}

    def setup(self):
        # setup connection to store server, i.e., db, redis, mongodb, etc.
        pass

    def close(self):
        # close connection to store server
        pass

    def getorder(self, ref):
        oid = None
        try:
            oid = self.ref2ordmap[ref]
        except KeyError:
            pass

        if oid is None:
            return None
        else:
            # TODO: get order
            pass

    def updateorder(self, order, oref):
        if oref in self.ref2ordmap:
            # existing order, just update
            pass
        else:
            # new order, create new oid and save
            oid = UUID.uuid1().int
            self.ref2ordmap[oref] = oid
            # TODO: and save the order
