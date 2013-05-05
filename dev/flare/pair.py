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
        Thread.__init__(self, ptf, qrediscfg, engine)

        self.qrepo = redis.Redis(
                host=rediscfg.host,
                port=rediscfg.port,
                db=rediscfg.repodb
                )
        self.qchannel = rediscfg.qchannel
        self.qsub = self.qrepo.pubsub()

        # a set of instruments the strategy works on
        # portfolio is a dict of code->amount, with minus
        # amount as shorting.
        self.ptf = ptf
        self.inst = set(pft.keys())

        # current order in going
        self.curorder = []

        # positions, code->(amount, price), in average
        self.position = {}

        # traded orders' uuids
        self.trade = []

        self.runflag = True
        self.logger = logging.getLogger()
        self.name = self.__class__.__name__

    def stop(self):
        self.runflag = False

    def submitptf(self, openclose):
        for inst in self.inst:
            r, oid = self.engine.doorder(inst, openclose, 0, self.ptf[inst],
                    ismktprice=True, isIOC=True, callobj=self)
            if 0 == r:
                self.curorder.append(oid)
            else:
                # TODO: submit error!
                pass

    def run(self):
        self.qsub.subscribe(self.qchannel)
        while self.runflag:
            qmsg = next(self.pubsub.listen())
            if qmsg['type'] == 'message':
                qdata = pickle.loads(qmsg['data'])
                if qdata.InstrumentID in self.inst:
                    act = self.onquote(qdata)
                    if act == 'open':
                        self.submitptf('open')
                    elif act == 'close':
                        self.submitptf('close')
                    else:
                        pass

    def onquote(self, q):
        pass

    def onOrderErr(self, order):
        pass

    def onOrderAccepted(self, order):
        pass

    def onOrderPartialTrade(self, order):
        pass

    def OnOrderFullyTrade(self, order):
        pass

    def onOrderCancelErr(self, order):
        pass

    def onOrderCancelled(self, order):
        pass


# start quote server

# start orderman: a naive one

# start accountman: only maintains positions and position limits

# start engine, with trading handler installed

# start pair trading strategy signal

