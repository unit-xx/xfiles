# paired arbitrage between IF futures

import sys
import config
import logging
from threading import Thread

import redis

import util
import flare_lib as flib

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
        self.engine.regstrat('sprd', self)
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

    # invoked by ctp callbacks
    def onOrderInsertErr(self, oid):
        pass

    def onOrderAccepted(self, oid):
        pass

    def onOrderPartialTrade(self, oid):
        pass

    def OnOrderFullyTrade(self, oid):
        pass

    def onOrderCancelErr(self, oid):
        pass

    def onOrderCancelled(self, oid):
        pass

    def onOrderTrade(self, oid, price, volume):
        pass


def main():

    # read config
    cfg = util.parse_config()

    # start quote server
    INST = ['IF1306', 'IF1307', 'IF1309', 'IF1312']
    q = flib.qrepo(INSTS, cfg.mduser, cfg.redis)
    q.setup()

    # start orderman
    ordman = flib.orderman(cfg.redis)
    ordman.setup()

    # start accountman: only maintains positions and position limits

    # start engine, with trading handler installed
    engine = flib.engine(cfg.trader, ordman, q)
    engine.setup()

    # start pair trading strategy signal
    ptf = {}
    mm = mmstrat(ptf, cfg.redis, engine)
    mm.start()

    # run untile Ctrl-C
    while 1:
        time.sleep(1)

    mm.stop()
    mm.join()

    engine.stop()

    orderman.stop()

    q.stop()

if __name__=='__main__':
    main()
