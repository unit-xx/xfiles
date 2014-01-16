# paired arbitrage between IF futures

import sys
import logging
import time
from threading import Thread
import cPickle as pickle
from collections import defaultdict

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
        self.qrepo.publish(self.qchannel, 'stop')

    def run(self):
        self.qsub.subscribe([self.machannel, self.qchannel])
        self.stratname = 'sprd'
        self.engine.regstrat(self.stratname, self)

        ma = defaultdict(dict)
        quote = defaultdict(dict)
        madiff = None
        madiffR = None

        sprdbid = 0.0
        sprdask = 0.0

        sigma = self.mmparam.sigma
        t = self.mmparam.t
        threshold = t + sigma/2
        qmax = self.mmparam.qmax
        qhold = 0

        # sim-trade
        wealth = 0.0
        txcost = 0.2
        ntrd = 0

        c1 = self.ptf[0]['code']
        c2 = self.ptf[1]['code']
        if self.ptf[0]['volume'] > 0 or self.ptf[1]['volume'] < 0:
            # first entry should be the short leg and the next one
            # is the long leg.
            self.logger.error('Portfolio mismatch.')
            return

        while self.runflag:
            qmsg = next(self.qsub.listen())

            if qmsg['type'] == 'message':

                # stop message
                if len(qmsg['data'])==4 and qmsg['data']=='stop':
                    continue

                if qmsg['channel'] == self.qchannel:
                    # receving a quotation update
                    q = pickle.loads(qmsg['data'])
                    c = q['code']
                    if c in self.inst:
                        quote[c] = q

                    try:
                        if (quote[c1]['tic']-quote[c2]['tic']) < 1e-6:
                            sprdbid = quote[c1]['bid1'] - quote[c2]['ask1']
                            sprdask = quote[c1]['ask1'] - quote[c2]['bid1']
                            deltaA = sprdbid - madiffR
                            deltaB = madiffR - sprdask

                            tdir = 0
                            if deltaA > threshold:
                                # suitable for short
                                if qhold > -qmax:
                                    tdir = -1

                                    wealth = wealth + sprdbid
                                    ntrd = ntrd + 1

                                    if qhold > 0:
                                        # do close long
                                        pass
                                    else:
                                        pass 
                                        # do open short
                                        # short if2, long if1

                            elif deltaB > threshold:
                                # suitable for long
                                if qhold < qmax:
                                    tdir = 1

                                    wealth = wealth - sprdask
                                    ntrd = ntrd + 1

                                    if qhold < 0:
                                        pass
                                        # do close short
                                    else:
                                        pass
                                        # do open long
                                        # long if2, short if1

                            else:
                                # nop
                                pass

                            if tdir != 0:
                                # logging. qhold/madiff/madiffR etc. are values 
                                # before trading. 
                                self.logger.info('[%s.%03d] (%+d) %+d %.2f %.2f %.2f %.2f %.2f %.2f %.2f %s %.2f %.2f %s %.2f %.2f',
                                        q['time'], q['msec'],
                                        tdir, qhold, threshold, deltaA, deltaB,
                                        madiff, madiffR, sprdask, sprdbid,
                                        c1, quote[c1]['ask1'], quote[c1]['bid1'],
                                        c2, quote[c2]['ask1'], quote[c2]['bid1'],
                                        )

                                # make changes
                                qhold += tdir
                                madiffR = madiff - qhold * sigma

                                # wealth are after trading
                                if qhold==0:
                                    self.logger.info('w=%.2f (%.2f), ntrd=%d',
                                            wealth, wealth-ntrd*txcost, ntrd)


                            # TODO: send order if sprd is large enough
                            # record what we see and what we get on trade
                            # don't go on next order before the current is fully traded.
                            # stat to maintain: q, oid/progress for two legs.
                            # warning when dangling leg exists long enough.
                    except KeyError:
                        pass
                    except TypeError:
                        pass

                elif qmsg['channel'] == self.machannel:
                    # a MA update
                    qma = pickle.loads(qmsg['data'])
                    if qma[0] in self.inst:
                        ma[qma[0]]['tick'] = qma[1]
                        ma[qma[0]]['val'] = qma[2]

                    try:
                        if ma[c1]['tick']==ma[c2]['tick']:
                            madiff = ma[c1]['val']-ma[c2]['val']
                            madiffR = madiff - qhold * sigma
                            #self.logger.info('madiff: %.2f', madiff)
                    except KeyError:
                        # no ma has been received
                        pass
                    except TypeError:
                        # ma is none since not enough quotes is accumulated to calc ma
                        pass

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
    ptf = [
            {'code':'IF1309', 'volume':-1},
            {'code':'IF1308', 'volume':1},
            ]
    INSTS = [x['code'] for x in ptf]
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
    mm = mmstrat(ptf, cfg.mmparam, cfg.redis, engine, ordman)
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
# $Id$ 
