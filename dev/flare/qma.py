# a standalone MA calculator which publish the results (through redis).

from collections import defaultdict, OrderedDict

from MdApi import MdApi, MdSpi
from TraderApi import TraderApi, TraderSpi  
import UserApiStruct as ustruct
import UserApiType as utype

import redis

import flaredef as fdef

class qMA(MdSpi):
    def __init__(self,
            instruments,
            mdcfg,
            rediscfg,
            qmaparam
        ):
        self.instruments = instruments
        self.broker_id = mdcfg.broker_id
        self.investor_id = mdcfg.investor_id
        self.passwd = mdcfg.passwd
        self.mdcfg = mdcfg
        self.rediscfg = rediscfg
        self.qmaparam = qmaparam
        self.reqid = 1

        # code -> lastest MA, using mid-price
        self.ma = {}
        # code -> buffer unit
        self.buf = defaultdict(OrderedDict)
        self.buflen = defaultdict(defaultdict(float))
        self.bufsum = defaultdict(defaultdict(float))
        # code -> current buffer tick unit
        self.curbufunit = {}

        self.logger = logging.getLogger()
        self.name = self.__class__.__name__
        self.quote = {}
        self.qlock = Lock()

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

    def OnRtnDepthMarketData(self, q):
        if q is None:
            return

        # calc q's time
        try:
            ticktp = [int(x) for x in q.UpdateTime.split(':')]
            tick = ticktp[0] * 3600 + ticktp[1] * 60 + ticktp[2] + q.UpdateMillisec/1000
        except IndexError:
            return

        # tick unit: which chuck does this tick belongs.
        inst = q.InstrumentID
        tu = int(tick/self.qmaparam.step)
        if tu != self.curbufunit[inst]
            for i in range(self.curbufunit[inst]+1, tu+1):
                # add and padding new buffer until the latest tick unit
                self.buf[inst].setdefault(i, [])
                # update unit lengths
                self.buflen[inst][i] = length(self.buf[inst][i])
                self.bufsum[inst][i] = sum(self.buf[inst][i])

            # update current buffer unit
            shift = tu - self.curbufunit[inst]
            self.curbufunit[inst] = tu

            # update MA value
            tsum = 0.0
            tlen = 0.0
            if tu > self.qmaparam.wsize:
                for i in range():
                    tsum += self.bufsum[inst][i]
                    tlen += self.buflen[inst][i]
                try:
                    maval = tsum/tlen
                except ZeroDivisionError:
                    maval = None

            # publish MA value
            self.r.publish(xxchannel, maval)

        # insert new quotes
        self.buf[inst][tu].append((q.BidPrice1+q.AskPrice1)/2)

        #print depth_market_data.InstrumentID,depth_market_data.BidPrice1,depth_market_data.BidVolume1,depth_market_data.AskPrice1,depth_market_data.AskVolume1,depth_market_data.LastPrice,depth_market_data.Volume,depth_market_data.UpdateTime,depth_market_data.UpdateMillisec

    def setup(self):
        # don't need to store mdapi, after calling
        # RegisterSpi, we have .api attribute automatically
        self.repo = redis.Redis(
                host=self.rediscfg.host,
                port=self.rediscfg.port,
                db=self.rediscfg.repodb
                )
        self.qmachannel = self.rediscfg.qmachannel

        mdapi = MdApi.CreateMdApi(self.name)
        mdapi.RegisterSpi(self)
        mdapi.RegisterFront(self.mdcfg.port)
        mdapi.Init()

        return True

    def stop(self):
        self.api.Release()
