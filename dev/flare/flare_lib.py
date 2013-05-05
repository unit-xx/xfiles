import sys
#reload(sys)
#sys.setdefaultencoding('gbk')

import logging
import Queue
from threading import Thread, currentThread, Lock, Event
from datetime import datetime
import uuid
import cPickle as pickle

from MdApi import MdApi, MdSpi
from TraderApi import TraderApi, TraderSpi  
import UserApiStruct as ustruct
import UserApiType as utype

import redis

class qrepo(MdSpi):
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

        self.repo = redis.Redis(
                host=rediscfg.host,
                port=rediscfg.port,
                db=rediscfg.repodb
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
            self.repo.publish(self.qchannel, q)
            self.repo.set(depth_market_data.InstrumentID, q)
            #print depth_market_data.InstrumentID,depth_market_data.BidPrice1,depth_market_data.BidVolume1,depth_market_data.AskPrice1,depth_market_data.AskVolume1,depth_market_data.LastPrice,depth_market_data.Volume,depth_market_data.UpdateTime,depth_market_data.UpdateMillisec
        finally:
            self.qlock.release()

    def getquote(self, inst):
        self.qlock.acquire()
        self.qlock.release()

    def setup(self)
        # don't need to store mdapi, after calling
        # RegisterSpi, we have .api attribute automatically
        mdapi = MdApi.CreateMdApi(self.name)
        mdapi.RegisterSpi(self)
        mdapi.RegisterFront(self.mdcfg.port)
        mdapi.Init()
        return True

class engine(TraderSpi):
    def __init__(self, tradercfg, tcap=10, orderman, qrepo):
        self.broker_id = tradercfg.broker_id
        self.investor_id = tradercfg.investor_id
        self.passwd = tradercfg.passwd
        self.tradercfg = tradercfg

        self.logger = logging.getLogger()
        self.name = self.__class__.__name__

        self.islogin = False
        self.loginevent = Event()
        self.loginevent.clear()

        self.tqueue = Queue.Queue()
        self.tqlock = Lock()
        self.tcap = tcap
        self.tpool = []

        self.reqid = 1
        self.reqlock = Lock()

        self.frontid = 0
        self.sessionid = 0
        self.oref = 0
        self.oreflock = Lock()

        self.orderman = orderman
        self.qrepo = qrepo

        self.oref2objmap = {}

        # saved order field, read from config
        self.sof = []

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
            self.islogin = False
            return
        self.logger.info(u'TD:trader login success')
        self.islogin = True
        self.frontid = userlogin.FrontID
        self.sessionid = userlogin.SessionID
        self.oref = int(userlogin.MaxOrderRef)
        self.savesession(self.frontid, self.sessionid,
                str(datetime.today().date()))
        self.loginevent.set()
        # TODO: save the session (sessionid, frontid, etc.) in
        # db for order booking and exporting.

    def setup(self)
        # start thread pool
        # start ctp api
        trader = TraderApi.CreateTraderApi(self.name)
        trader.RegisterSpi(self)
        trader.SubscribePublicTopic(THOST_TERT_QUICK)
        trader.SubscribePrivateTopic(THOST_TERT_QUICK)
        trader.RegisterFront(cuser.port)
        trader.Init()
        self.loginevent.wait()
        return self.islogin

    def savesession(frontid, sessionid, date):
        # a too simple logging
        f = open('sessionlog.log'. 'a')
        f.writelines(['%d, %d, %s' % (frontid, sessionid, date), '\n'])
        f.close()

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

    def makeoreftp(self, oref):
        return (self.frontid, self.sessionid, oref)

    def doorder(self, inst, openclose, price, volume,
            ismktprice=False, isIOC=False, callobj=None):
        # minus volume as short
        oref = self.inc_order_ref()
        oreftp = self.makeoreftp(oref)
        oid = self.orderman.insertorder(oreftp)
        if callobj:
            self.oref2objmap[oreftp] = callobj
            # TODO: in callbacks, find callobj by oref and call its handler 

        req = ustruct.InputOrder(
                InstrumentID = inst,
                Direction = utype.THOST_FTDC_D_Buy if (volume>0) else utype.THOST_FTDC_D_Sell,
                OrderRef = str(oref),
                LimitPrice = 0 if ismktprice else price,
                VolumeTotalOriginal = volume if (volume>0) else -volume,
                OrderPriceType = utype.THOST_FTDC_OPT_AnyPrice if ismktprice else utype.THOST_FTDC_OPT_LimitPrice,
                BrokerID = self.cuser.broker_id,
                InvestorID = self.cuser.investor_id,
                CombOffsetFlag = utype.THOST_FTDC_OF_Open if (openclose=='open') else utype.THOST_FTDC_OF_Close,
                CombHedgeFlag = utype.THOST_FTDC_HF_Speculation,
                VolumeCondition = utype.THOST_FTDC_VC_AV,
                MinVolume = 1,
                ForceCloseReason = utype.THOST_FTDC_FCC_NotForceClose,
                IsAutoSuspend = 1, # 1 or 0?
                #UserForceClose = 0, not a field in doc, a obsoleted parameter?
                TimeCondition = utype.THOST_FTDC_TC_IOC if isIOC else utype.THOST_FTDC_TC_GFD,
            )

        logging.info(u'下单: instrument=%s,openclose=%s,amount=%s,price=%s,ismktprice=%d,OrderRef=%d,oid=%d'
                % (order.instrument, openclose,
                    volume, price, str(ismktprice), oref, oid))
        r = self.trader.ReqOrderInsert(req, self.inc_request_id())
        return r, oid

    # trade handlers, save orders and call object's handlers.
    def OnRspOrderInsert(self, pInputOrder, pRspInfo, nRequestID, bIsLast):
        '''
            报单未通过参数校验,被CTP拒绝
            正常情况后不应该出现
        '''
        # TODO: summarize common field of porder and ptrade
        return

    def OnErrRtnOrderInsert(self, pInputOrder, pRspInfo):
        '''
            交易所报单录入错误回报
            正常情况后不应该出现
            这个回报没有request_id
        '''

    def OnRtnOrder(self, pOrder):
        ''' 报单通知
            CTP、交易所接受报单
            Agent中不区分，所得信息只用于撤单
        '''
        if pOrder.OrderStatus == utype.THOST_FTDC_OST_Unknown:
            #CTP接受，但未发到交易所
        elif pOrder.OrderStatus == utype.THOST_FTDC_OST_Canceled:
            # order is cancelled
        else:
            # 交易所接受Order

        return

    def OnRtnTrade(self, pTrade):
        '''
        成交通知
        '''

    
    def OnRspOrderAction(self, pInputOrderAction, pRspInfo, nRequestID, bIsLast):
        '''
            ctp撤单校验错误
        '''

    def OnErrRtnOrderAction(self, pOrderAction, pRspInfo):
        ''' 
            交易所撤单操作错误回报
            正常情况后不应该出现
        '''


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
    3. also manages positions, combos
    '''
    def __init__(self, omrediscfg):
        # oref is a tuple of (frontid, sessionid, orderref)
        self.oref2ordmap = {}
        self.rediscfg = omrediscfg

    def setup(self):
        # setup connection to store server, i.e., db, redis, mongodb, etc.
        self.orderdb = redis.Redis(
                host=rediscfg.host,
                port=rediscfg.port,
                db=rediscfg.odb
                )
        return True

    def close(self):
        # close connection to store server
        self.orderdb.bgsave()

    def getorder(self, oref):
        # oref is a tuple of (frontid, sessionid, orderref)
        if oref in self.oref2ordmap:
            oid = self.oref2ordmap[oref]
            return self.orderdb.hgetall(oid)
        else:
            return None

    def insertorder(self, oref):
        # oref is a tuple of (frontid, sessionid, orderref)
        # insert new order
        # order fields may include time, order price, deal price, etc.
        oid = uuid.uuid1().int
        self.oref2ordmap[oref] = oid
        return oid

    def updateorder(self, order, oref):
        # oref is a tuple of (frontid, sessionid, orderref)
        if oref not in self.ref2ordmap:
            # new order, create new oid and save
            oid = self.insertorder(oref)
        self.orderdb.hmset(oid, order)

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

class strategy(Thread):
    '''
    a interface for implementing strategies

    1. strategy is a thread, which constantly receiving quotes and
    update signal
    2. strategy `instances' are record in the class and save in datastore.
    '''
    def __init__(self):
        Thread.__init__(self, inst, rediscfg)

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

