# paired arbitrage between IF futures

import sys
import logging
import time
from threading import Thread
import cPickle as pickle

import redis

import util
import flare_lib as flib

class mmstrat(Thread):
    '''
    qmax, current positions
    '''
    def __init__(self, ptf, mmparam, rediscfg, engine, orderman):
        Thread.__init__(self)

        self.qrepo = redis.Redis(
                host=rediscfg.host,
                port=rediscfg.port,
                db=rediscfg.repodb
                )
        self.qchannel = rediscfg.qchannel
        self.machannel = rediscfg.machannel
        self.qsub = self.qrepo.pubsub()
        self.engine = engine
        self.orderman = orderman

        # a set of instruments the strategy works on
        # portfolio is a dict of code->amount, with minus
        # amount as shorting.
        self.ptf = ptf
        self.inst = set([x['code'] for x in ptf])

        self.mmparam = mmparam


        # current order in going
        self.curorder = []

        # positions, code->(amount, price), in average
        self.position = {}

        # traded orders' uuids
        self.trade = []

        self.runflag = True
        self.logger = logging.getLogger()
        self.name = self.__class__.__name__

        self.did = False

    def stop(self):
        self.runflag = False
        self.qrepo.publish(self.machannel, 'stop')

    def run(self):
        self.qsub.subscribe(self.machannel)
        self.stratname = 'sprd'
        self.engine.regstrat(self.stratname, self)
        while self.runflag:
            qmsg = next(self.qsub.listen())

            if qmsg['type'] == 'message':

                if len(qmsg['data'])==4 and qmsg['data']=='stop':
                    continue

                qdata = pickle.loads(qmsg['data'])
                if qdata[0] in self.inst:
                    self.onquote(qdata)
                    # TODO: calc ma diff and submit order

    # invoked by ctp callbacks
    def onOrderInsertErr(self, oid):
        order, olk = self.orderman.getorder(oid)
        with olk:
            self.logger.info(str(order))

    def onOrderAccepted(self, oid):
        order, olk = self.orderman.getorder(oid)
        with olk:
            self.logger.info(str(order))

    def onOrderPartialTrade(self, oid):
        pass

    def onOrderFullyTrade(self, oid):
        order, olk = self.orderman.getorder(oid)
        with olk:
            self.logger.info(str(order))

    def onOrderCancelErr(self, oid):
        pass

    def onOrderCancelled(self, oid):
        order, olk = self.orderman.getorder(oid)
        with olk:
            self.logger.info(str(order))

    def onOrderTrade(self, oid, price, volume):
        t, tlk = self.orderman.gettrade(oid)
        with tlk:
            self.logger.info(t)


def main():

    # read config
    cfg = util.parse_config('pair')
    logger = logging.getLogger()

    # start quote server
    INSTS = ['IF1306', 'IF1307', 'IF1309', 'IF1312']
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
    ptf = [
            #{'code':'IF1307', 'amount':-1},
            {'code':'IF1306', 'amount':1},
            ]
    mm = mmstrat(ptf, cfg.redis, engine, ordman)
    mm.start()

    # run untile Ctrl-C
    try:
        while 1:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    logger.info('stopping...')
    logger.info('\tmm...')
    mm.stop()
    mm.join()

    logger.info('\tengine...')
    engine.stop()

    logger.info('\torderman...')
    ordman.stop()

    logger.info('\tqrepo...')
    q.stop()

if __name__=='__main__':
    main()
