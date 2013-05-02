import sys
#reload(sys)
#sys.setdefaultencoding('gbk')

import logging
import Queue
from threading import Thread, currentThread, Lock, Event
import uuid
import pickle

from MdApi import MdApi, MdSpi
from TraderApi import TraderApi, TraderSpi  
import UserApiStruct as ustruct
import UserApiType as utype

import redis

from util import import BaseObject

class qserver(MdSpi):

    def __init__(self,
            instruments,
            mdcfg,
            rediscfg
        ):
        self.instruments = instruments
        self.broker_id = mdcfg.broker_id
        self.investor_id = mdcfg.investor_id
        self.passwd = mdcfg.passwd
        self.mdcfg = mdcfg
        self.reqid = 1

        self.qrepo = redis.Redis(
                host=rediscfg.host,
                port=rediscfg.port,
                db=rediscfg.qrepodb
                )
        self.qchannel = rediscfg.qchannel

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
        self.logger.info(u'front disconnected, reason:%s' % (reason,))

    def OnFrontConnected(self):
        self.logger.info(u'front connected')
        self.user_login(self.broker_id, self.investor_id, self.passwd)

    def user_login(self, broker_id, investor_id, passwd):
        req = ustruct.ReqUserLogin(BrokerID=broker_id, UserID=investor_id, Password=passwd)
        r=self.api.ReqUserLogin(req, self.inc_request_id())

    def OnRspUserLogin(self, userlogin, info, rid, is_last):
        self.logger.info(u'user login, info:%s, rid:%s, is_last:%s' % (info, rid, is_last))
        if is_last and self.isRspSuccess(info):
            self.api.SubscribeMarketData(self.instruments)

    def OnRtnDepthMarketData(self, depth_market_data):
        try:
            self.qlock.acquire()
            q = pickle.dumps(depth_market_data)
            self.qrepo.publish(self.qchannel, q)
            self.qrepo.set(depth_market_data.InstrumentID, q)
            #print depth_market_data.InstrumentID,depth_market_data.BidPrice1,depth_market_data.BidVolume1,depth_market_data.AskPrice1,depth_market_data.AskVolume1,depth_market_data.LastPrice,depth_market_data.Volume,depth_market_data.UpdateTime,depth_market_data.UpdateMillisec
        finally:
            self.qlock.release()

    def getquote(self, inst):
        self.qlock.acquire()
        self.qlock.release()

    def setup(self, name='qserver'):
        # don't need to store mdapi, after calling
        # RegisterSpi, we have .api attribute automatically
        mdapi = MdApi.CreateMdApi(name)
        mdapi.RegisterSpi(self)
        mdapi.RegisterFront(self.mdcfg.port)
        mdapi.Init()

class engine(TraderSpi):
    def __init__(self, tradercfg, tcap=10, orderman):
        self.broker_id = tradercfg.broker_id
        self.investor_id = tradercfg.investor_id
        self.passwd = tradercfg.passwd
        self.tradercfg = tradercfg

        self.logger = logging.getLogger()
        self.name = self.__class__.__name__

        self.tqueue = Queue.Queue()
        self.tqlock = Lock()
        self.tcap = tcap
        self.tpool = []

        self.reqid = 1
        self.reqlock = Lock()

        self.frontid = 0
        self.sessionid = 0
        self.oref = 0

        self.orderman = orderman


    def isRspSuccess(self, RspInfo):
        return RspInfo == None or RspInfo.ErrorID == 0

    def OnFrontDisConnected(self, reason):
        self.logger.info(u'front disconnected, reason:%s' % (reason,))

    def OnFrontConnected(self):
        self.logger.info(u'front connected')
        self.user_login(self.broker_id, self.investor_id, self.passwd)

    def user_login(self, broker_id, investor_id, passwd):
        req = ustruct.ReqUserLogin(BrokerID=broker_id, UserID=investor_id, Password=passwd)
        r=self.api.ReqUserLogin(req, self.inc_request_id())

    def OnRspUserLogin(self, userlogin, info, rid, is_last):
        self.logger.info(u'trader login, info:%s, rid:%s, is_last:%s' % (info, rid, is_last))
        if not self.isRspSuccess(info):
            self.logger.warning(u'trader login failed')
            return
        self.logger.info(u'TD:trader login success')
        self.front_id = userlogin.FrontID
        self.session_id = userlogin.SessionID
        self.order_ref = int(userlogin.MaxOrderRef)

    def setup(self):
        # start thread pool
        # start ctp api

    def inc_request_id(self):
        ret = 0 
        with self.reqlock:
            self.reqid += 1
            ret = self.reqid
        return ret

    def inc_order_ref(self):
        ret = 0 
        with self.oreflock:
            self.oref += 1
            ret = self.oref
        return ret

    def putorder(self, order):
        # put order into queue
        pass

    def doorder(self, inst, direction, openclose, price, volume, ismktprice):
        oref = self.inc_order_ref()
        req = ustruct.InputOrder(
                InstrumentID = inst,
                Direction = utype.THOST_FTDC_D_Buy if (direction=='buy') else utype.THOST_FTDC_OF_Close,
                OrderRef = str(oref),
                LimitPrice = 0 if ismktprice else price,
                VolumeTotalOriginal = volume,
                OrderPriceType = utype.THOST_FTDC_OPT_AnyPrice if ismktprice else utype.THOST_FTDC_OPT_LimitPrice,
                
                BrokerID = self.cuser.broker_id,
                InvestorID = self.cuser.investor_id,
                CombOffsetFlag = utype.THOST_FTDC_OF_Open if (openclose=='open') else utype.THOST_FTDC_OF_Close,         #开仓 5位字符,但是只用到第0位
                CombHedgeFlag = utype.THOST_FTDC_HF_Speculation,   #投机 5位字符,但是只用到第0位

                VolumeCondition = utype.THOST_FTDC_VC_AV,
                MinVolume = 1,  #这个作用有点不确定,有的文档设成0了
                ForceCloseReason = utype.THOST_FTDC_FCC_NotForceClose,
                IsAutoSuspend = 1,
                UserForceClose = 0,
                TimeCondition = utype.THOST_FTDC_TC_GFD,
            )
        # TODO: save order in meme for access in callbacks
        #       add entry in ref2order map
        #       seems no need to save every orders in db, 
        #       add virtual account, session mapping at connection
        #       should be enough (need conform).

        logging.info(u'下单: instrument=%s,方向=%s,开平=%s,数量=%s,价格=%s,市价=%d,OrderRef=%d' % (order.instrument, direction, openclose, volume, price, str(ismktprice), oref))
        r = self.trader.ReqOrderInsert(req, self.inc_request_id())
        return r

class engine_worker(Thread):
    def __init__(self, engine, qserv):
        Thread.__init__(self)
        self.tqueue = engine.tqueue
        self.engine = engine
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
            oid = uuid.uuid1().int
            self.ref2ordmap[oref] = oid
            # TODO: and save the order

class accountman:
    '''
    1. maintains positions and cash account
    2. set limitations
    '''
    def __init__(self):
        pass

    def getpos(inst, direction):
        pass

    def getcash():
        pass

    def getlimit(inst, direction):
        pass

class strategy:
    '''
    a interface for implementing strategies

    1. strategy is a thread, which constantly receiving quotes and
    update signal
    2. strategy `instances' are record in the class and save in datastore.
    '''
    def __init__(self):
        self.statemap = {}
        pass

    def onquote(self, q):
        pass

