# a standalone MA calculator which publish the results (through redis).

from collections import defaultdict, OrderedDict
import cPickle as pickle

from MdApi import MdApi, MdSpi
import UserApiStruct as ustruct
import UserApiType as utype

import redis

import flaredef as fdef

class qMA(MdSpi):
    def __init__(self,
            instruments,
            mdcfg,
            rediscfge
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
        self.buflen = defaultdict(defaultdict(float))
        self.bufsum = defaultdict(defaultdict(float))
        # code -> current buffer tick unit
        self.curbuf = {}

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

        # tick unit: which chunck does this tick belongs.
        inst = q.InstrumentID
        tu = int(tick/self.maparam.step)
        try:
            cbuf = self.curbuf[inst]
        except KeyError:
            self.curbuf[inst] = tu
            cbuf = tu

        if tu != cbuf
            for i in range(cbuf+1, tu+1):
                # add and padding new buffer until the latest tick unit
                self.buflen[inst][i] = 0.0
                self.bufsum[inst][i] = 0.0

            # update current buffer unit
            self.curbuf[inst] = tu

            # update MA value
            tsum = 0.0
            tlen = 0.0
            if len(self.buflen[inst]) >= self.maparam.wsize:
                for i in range(tu-wsize, tu):
                    tsum += self.bufsum[inst][i]
                    tlen += self.buflen[inst][i]
                try:
                    maval = tsum/tlen
                except ZeroDivisionError:
                    maval = None

            # publish MA value
            self.repo.publish(machannel, pickle.dumps((inst, tu, maval)))
            self.logger.info('new MA: %s %d %.2f' % (inst, tu, maval))

        # insert new quotes
        self.bufsum[inst][tu] += (q.BidPrice1+q.AskPrice1)/2
        self.buflen[inst][tu] += 1

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
