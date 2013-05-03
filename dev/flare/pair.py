# paired arbitrage between IF futures

import sys
import config
import logging
from threading import Thread

import redis

class mmstrat(Thread):
    '''
    qmax, current positions
    '''
    def __init__(self):
        Thread.__init__(self, inst, qrediscfg)

        self.qrepo = redis.Redis(
                host=rediscfg.host,
                port=rediscfg.port,
                db=rediscfg.repodb
                )
        self.qchannel = rediscfg.qchannel
        self.qsub = self.qrepo.pubsub()

        self.inst = set(inst) # a set of instruments the strategy works on
        
        self.statemap = {}

        self.runflag = True
        self.logger = logging.getLogger()
        self.name = self.__class__.__name__


    def stop(self):
        self.runflag = False

    def run(self):
        self.qsub.subscribe(self.qchannel)
        while self.runflag:
            qmsg = next(self.pubsub.listen())
            if qmsg['type'] == 'message':
                qdata = pickle.loads(qmsg['data'])
                if qdata.InstrumentID in self.inst:
                    self.onquote(qdata)

    def onquote(self, q):
        pass

# start quote server

# start orderman: a naive one

# start accountman: only maintains positions and position limits

# start engine, with trading handler installed

# start pair trading strategy signal

