# a standalone MA calculator which publish the results (through redis).

from collections import defaultdict, OrderedDict
import cPickle as pickle
import logging
import time

from MdApi import MdApi, MdSpi
import UserApiStruct as ustruct
import UserApiType as utype

import redis

import util

class qMA(MdSpi):
    def __init__(self,
            instruments,
            mdcfg,
            rediscfg,
            maparam
        ):
        self.instruments = instruments
        self.broker_id = mdcfg.broker_id
        self.investor_id = mdcfg.investor_id
        self.passwd = mdcfg.passwd
        self.mdcfg = mdcfg
        self.rediscfg = rediscfg
        self.maparam = maparam
        self.reqid = 1

        # code -> lastest MA, using mid-price
        self.ma = {}
        # code -> buffer unit
        self.buflen = defaultdict(list)
        self.bufsum = defaultdict(list)
        # code -> current buffer tick unit
        self.curbuf = {}
        self.lastvol = 0

        self.logger = logging.getLogger()
        self.name = self.__class__.__name__

    def inc_request_id(self):
        self.reqid += 1
        return self.reqid

    def isRspSuccess(self, RspInfo):
        return RspInfo == None or RspInfo.ErrorID == 0

    def OnFrontDisConnected(self, reason):
        self.logger.info(u'md front disconnected, reason:%s' % (reason,))

    def OnFrontConnected(self):
        self.logger.info(u'md front connected')
        self.user_login(self.broker_id, self.investor_id, self.passwd)

    def user_login(self, broker_id, investor_id, passwd):
        req = ustruct.ReqUserLogin(BrokerID=broker_id, UserID=investor_id, Password=passwd)
        r=self.api.ReqUserLogin(req, self.inc_request_id())

    def OnRspUserLogin(self, userlogin, info, rid, is_last):
        self.logger.info(u'md user login, info:%s, rid:%s, is_last:%s' % (info, rid, is_last))
        if is_last and self.isRspSuccess(info):
            self.api.SubscribeMarketData(self.instruments)
            self.logger.info('sub md: %s' % self.instruments)

    def qma1(self, q):
        try:
            ticktp = [int(x) for x in q.UpdateTime.split(':')]
            tick = ticktp[0] * 3600 + ticktp[1] * 60 + ticktp[2] + q.UpdateMillisec/1000.0
        except IndexError:
            return

        # tick unit: which chunck does this tick belongs.
        inst = q.InstrumentID
        tu = int(tick/self.maparam.step)

        # initialize
        try:
            cbuf = self.curbuf[inst]
        except KeyError:
            self.curbuf[inst] = tu
            self.buflen[inst][tu] = 0.0
            self.bufsum[inst][tu] = 0.0
            cbuf = tu

        if tu != cbuf:
            for i in range(cbuf+1, tu+1):
                # add and padding new buffer until the latest tick unit
                self.buflen[inst][i] = 0.0
                self.bufsum[inst][i] = 0.0

            # update current buffer unit
            self.curbuf[inst] = tu

            # update MA value
            tsum = 0.0
            tlen = 0.0
            maval = None
            if len(self.buflen[inst]) > self.maparam.wsize:
                #self.logger.info(self.bufsum[inst].keys())
                #self.logger.info(self.buflen[inst].keys())
                #self.logger.info(tu)
                #self.logger.info(self.maparam.wsize)

                for i in range(tu-self.maparam.wsize, tu):
                    tsum += self.bufsum[inst][i]
                    tlen += self.buflen[inst][i]
                try:
                    maval = tsum/tlen
                except ZeroDivisionError:
                    pass

            # publish MA value
            self.repo.publish(self.machannel, pickle.dumps((inst, tu, maval)))
            self.logger.info('new MA: %s %d %s' % (inst, tu, maval))

        # insert new quotes
        self.bufsum[inst][tu] += (q.BidPrice1+q.AskPrice1)/2
        self.buflen[inst][tu] += 1

    def qma2(self, q):
        inst = q.InstrumentID

        if len(self.buflen[inst]) == 0:
            # fully empty buffer
            self.buflen[inst].append(0.0)
            self.bufsum[inst].append(0.0)

        if self.buflen[inst][-1] < self.maparam.bufmax:
            # accumulate in current buffer
            self.buflen[inst][-1] +=1
            self.bufsum[inst][-1] += (q.BidPrice1+q.AskPrice1)/2
        else:
            # current buffer is long enough, so...
            # publish new MA
            blen = len(self.buflen[inst])
            tsum = 0.0
            tlen = 0.0
            maval = 0.0
            tu = blen # backward compatible with qma1
            if blen > self.maparam.wsize:
                for i in range(blen-self.maparam.wsize, blen):
                    tlen += self.buflen[inst][i]
                    tsum += self.bufsum[inst][i]
                maval = tsum/tlen
                self.repo.publish(self.machannel, pickle.dumps((inst, tu, maval)))
                self.logger.info('new MA: %s %d %s' % (inst, tu, maval))

            # add new entry in buflen/bufsum
            self.buflen[inst].append(1.0)
            self.bufsum[inst].append((q.BidPrice1+q.AskPrice1)/2)

        #self.logger.info(self.buflen[inst])
        #self.logger.info(self.bufsum[inst])
        #self.logger.info(len(self.buflen[inst]))
        #self.logger.info('======')

    def OnRtnDepthMarketData(self, q):
        if q is None:
            return

        if q.BidPrice1 > q.UpperLimitPrice or q.BidPrice1 < q.LowerLimitPrice:
            return

        if q.AskPrice1 > q.UpperLimitPrice or q.AskPrice1 < q.LowerLimitPrice:
            return

        self.qma2(q)

        #self.logger.info('%s %s %s', q.InstrumentID, q.LastPrice, q.Volume-self.lastvol)
        #self.lastvol = q.Volume
        # calc q's time


    def setup(self):
        # don't need to store mdapi, after calling
        # RegisterSpi, we have .api attribute automatically
        self.repo = redis.Redis(
                host=self.rediscfg.host,
                port=self.rediscfg.port,
                db=self.rediscfg.repodb
                )
        self.machannel = self.rediscfg.machannel

        mdapi = MdApi.CreateMdApi(self.name)
        mdapi.RegisterSpi(self)
        mdapi.RegisterFront(self.mdcfg.port)
        mdapi.Init()

        return True

    def stop(self):
        self.api.Release()

def main():
    cfg = util.parse_config('qma')
    logger = logging.getLogger()

    # start quote server
    INSTS = ['IF1308', 'IF1309']#, 'IF1309', 'IF1312']
    q = qMA(INSTS, cfg.mduser, cfg.redis, cfg.maparam)
    q.setup()

    while 1:
        time.sleep(1)

if __name__=='__main__':
    main()
# $Id$ 
