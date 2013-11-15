# flare library in message passing style.
# flame = flare in message

import logging

import redis

from MdApi import MdApi, MdSpi
from TraderApi import TraderApi, TraderSpi  
import UserApiStruct as ustruct
import UserApiType as utype

class redispubsub:
    def __init__(self, rconfig):
        self.rconfig = rconfig
        return

    def setup(self):
        self.redis = redis.Redis(
                host=self.rconfig.host,
                port=self.rconfig.port,
                db=self.rconfig.repodb
                )

        self.pubsub = self.redis.pubsub()

    def pub(self, channel, msg):
        self.redis.publish(channel, msg)

    def sub(self, channel):
        self.pubsub.subscribe(channel)

    def listen(self):
        return self.pubsub.listen()

KVstore = redis.Redis
PubSub = redispubsub

class qrepo(MdSpi):
    '''
    Receive quotes from CTP and 1) publish, 2) store quotes.
    Assumed to run as a single thread.
    '''
    def __init__(self, instruments, mdconfig, pubsub, store):
        self.instruments = instruments
        self.broker_id = mdconfig.broker_id
        self.investor_id = mdconfig.investor_id
        self.passwd = mdconfig.passwd
        self.mdcfg = mdconfig
        self.store = store
        self.reqid = 1

        self.logger = logging.getLogger()
        self.name = self.__class__.__name__

    def inc_request_id(self):
        self.reqid += 1
        return self.reqid

    def isRspSuccess(self, RspInfo):
        return RspInfo == None or RspInfo.ErrorID == 0

    def OnFrontDisConnected(self, reason):
        self.logger.info('Disconnected to CTP quote server (%s).' % (reason,))

    def OnFrontConnected(self):
        self.user_login(self.broker_id, self.investor_id, self.passwd)

    def user_login(self, broker_id, investor_id, passwd):
        req = ustruct.ReqUserLogin(BrokerID=broker_id, UserID=investor_id, Password=passwd)
        r=self.api.ReqUserLogin(req, self.inc_request_id())

    def OnRspUserLogin(self, userlogin, info, rid, is_last):
        if self.isRspSuccess(info):
            if is_last:
                self.api.SubscribeMarketData(self.instruments)
                self.logger.info('sub md: %s' % self.instruments)
        else:
            self.logger.info('Login failed: %s.', info)

    def OnRtnDepthMarketData(self, q):
        tic = float(q.UpdateTime[-2:]) + float(q.UpdateTime[-5:-3])*60 + q.UpdateMillisec/1000.0
        qq = {
                'bid1':q.BidPrice1,
                'bidvol1':q.BidVolume1,
                'ask1':q.AskPrice1,
                'askvol1':q.AskVolume1,
                'last':q.LastPrice,
                'time':q.UpdateTime,
                'msec':q.UpdateMillisec,
                'code':q.InstrumentID,
                'tic':tic
                    }
        # TODO: how to set qchannel
        self.pubsub.publish(self.qchannel, pickle.dumps(qq))
        self.store.xxx()

    def setup(self):
        # don't need to store mdapi, after calling
        # RegisterSpi, we have .api attribute automatically
        mdapi = MdApi.CreateMdApi(self.name)
        mdapi.RegisterSpi(self)
        mdapi.RegisterFront(self.mdcfg.port)
        mdapi.Init()
        return True

    def stop(self):
        self.api.Release()

class engine(Thread):
    '''
    engine works as a separate thread, which 
    '''
    def __init__(self):
        pass

    def 
