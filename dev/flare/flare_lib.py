import sys

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

import flaredef as fdef

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
        # TODO: is the locking redundant?, use dict instead of redis?
        try:
            q = pickle.dumps(depth_market_data)
            self.repo.publish(self.qchannel, q)
            self.qlock.acquire()
            self.repo.set(depth_market_data.InstrumentID, q)
            #print depth_market_data.InstrumentID,depth_market_data.BidPrice1,depth_market_data.BidVolume1,depth_market_data.AskPrice1,depth_market_data.AskVolume1,depth_market_data.LastPrice,depth_market_data.Volume,depth_market_data.UpdateTime,depth_market_data.UpdateMillisec
        finally:
            self.qlock.release()

    def getquote(self, inst):
        ret = None
        try:
            self.qlock.acquire()
            ret = self.repo.get(inst)
        finally:
            self.qlock.release()
        return ret

    def setup(self)
        # don't need to store mdapi, after calling
        # RegisterSpi, we have .api attribute automatically
        mdapi = MdApi.CreateMdApi(self.name)
        mdapi.RegisterSpi(self)
        mdapi.RegisterFront(self.mdcfg.port)
        mdapi.Init()
        return True

class engine(TraderSpi):
    def __init__(self, tradercfg, orderman, qrepo):
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
        self.tcap = tradercfg.tpoolcap
        self.tpool = []

        self.reqid = 1
        self.reqlock = Lock()

        self.frontid = 0
        self.sessionid = 0
        self.oref = 0
        self.oreflock = Lock()

        self.orderman = orderman
        self.qrepo = qrepo

        # TODO: use strats instead of oreftp2oid
        self.oreftp2obj = {}
        # get strats object from name
        self.strats = {}

        # mysession is set of tuples (front, session)
        # and is stored in redis (by orderman) in two list
        # and is recovered on engine setup()
        # so that we can filter out orders from other clients
        self.mysession = set()

    # helpers
    def isRspSuccess(self, RspInfo):
        return RspInfo == None or RspInfo.ErrorID == 0

    # login and setup
    def OnFrontDisConnected(self, reason):
        self.logger.info(u'front disconnected, reason:%s' % (reason,))
        self.islogin = False

    def OnFrontConnected(self):
        self.logger.info(u'front connected')
        self.user_login(self.broker_id, self.investor_id, self.passwd)

    def user_login(self, broker_id, investor_id, passwd):
        req = ustruct.ReqUserLogin(BrokerID=broker_id, UserID=investor_id, Password=passwd)
        r=self.api.ReqUserLogin(req, self.inc_request_id())

    def OnRspUserLogin(self, userlogin, info, rid, is_last):
        self.logger.info(u'trader login, info:%s, rid:%s, is_last:%s' % (info, rid, is_last))
        if self.isRspSuccess(info):
            self.logger.info(u'TD:trader login success')
            self.frontid = userlogin.FrontID
            self.sessionid = userlogin.SessionID
            self.oref = int(userlogin.MaxOrderRef)
            self.islogin = True
        else:
            self.logger.warning(u'trader login failed')
            self.islogin = False
        self.loginevent.set()

    def setup(self)
        # start thread pool
        # start ctp api
        trader = TraderApi.CreateTraderApi(self.name)
        trader.RegisterSpi(self)
        trader.SubscribePublicTopic(THOST_TERT_QUICK)
        trader.SubscribePrivateTopic(THOST_TERT_QUICK)
        trader.RegisterFront(self.cuser.port)
        trader.Init()
        self.loginevent.wait()

        if self.islogin:
            self.orderman.addlogin(self.frontid,
                    self.sessionid, self.GetTradingDay())

        return self.islogin

    def close(self):
        # stop ctp api
        # stop thread pool
        pass

    # order helpers
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

    def makeoreftp(self, oref):
        return (self.frontid, self.sessionid, oref)

    # orders and trades
    def doorder(self, inst, openclose, price, volume, prid, strat,
            ismktprice=False, isIOC=False, callobj=None):
        # minus volume as short

        # first we insert order quickly to store some key fields
        oreftp = self.makeoreftp(oref)
        oid = self.orderman.insertorder(oreftp, prid, strat)

        # then we submit order
        oref = self.inc_order_ref()
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
        r = self.trader.ReqOrderInsert(req, self.inc_request_id())
        self.logger.info(u'下单: instrument=%s,openclose=%s,amount=%s,price=%s,ismktprice=%d,OrderRef=%d,oid=%d'
                % (order.instrument, openclose,
                    volume, price, str(ismktprice), oref, oid))

        # finnaly, store orders completely in db
        # submit before save record, better performance
        # but may lost recored on crash
        self.orderman.updateorder(oreftp, req)
        return r, oid

    def OnRspOrderInsert(self, pInputOrder, pRspInfo, nRequestID, bIsLast):
        '''
            报单未通过参数校验,被CTP拒绝
            正常情况后不应该出现
        '''
        # TODO: when pRspInfo is error, pRspInfo logging
        oreftp = self.makeoreftp(pInputOrder.OrderRef)
        if self.orderman.ismysession(oreftp):
            try:
                callobj = self.oreftp2obj[oreftp]
            except KeyError:
                self.logging.warning('oreftp (%s) is not recored.' % str(oreftp))
            if callobj is not None:
                try:
                    callobj.onOrderInsertErr(pInputOrder)
                except Exception:
                    self.logger.exception('onOrderInsertErr')
            self.orderman.updateorder(pInputOrder, oreftp)
        return

    def OnErrRtnOrderInsert(self, pInputOrder, pRspInfo):
        '''
            交易所报单录入错误回报
            正常情况后不应该出现
            这个回报没有request_id
        '''
        oreftp = self.makeoreftp(pInputOrder.OrderRef)
        if self.orderman.ismysession(oreftp):
            try:
                callobj = self.oreftp2obj[oreftp]
            except KeyError:
                self.logging.warning('oreftp (%s) is not recored.' % str(oreftp))
            if callobj is not None:
                try:
                    callobj.onOrderInsertErr(pInputOrder)
                except Exception:
                    self.logger.exception('onOrderInsertErr')
            self.orderman.updateorder(pInputOrder, oreftp)
        return

    def OnRtnOrder(self, pOrder):
        ''' 报单通知
            CTP、交易所接受报单
            Agent中不区分，所得信息只用于撤单
        '''
        # TODO: which state indicates partial cancel?
        # TODO: update position and order trading status
        oreftp = self.makeoreftp(pOrder.OrderRef)
        if self.orderman.ismysession(oreftp):
            try:
                callobj = self.oreftp2obj[oreftp]
            except KeyError:
                self.logging.warning('oreftp (%s) is not recored.' % str(oreftp))
            if callobj is not None:
                if pOrder.OrderStatus in (utype.THOST_FTDC_OST_Unknown, utype.THOST_FTDC_OST_NotTouched):
                    #CTP接受，但未发到交易所
                    try:
                        self.callobj.onOrderAccepted(pOrder)
                    except Exception:
                        self.logger.exception('onOrderAccepted')
                elif pOrder.OrderStatus in (utype.THOST_FTDC_OST_Canceled,):
                    # order is cancelled
                    try:
                        self.callobj.onOrderCancelled(pOrder)
                    except Exception:
                        self.logger.exception('onOrderCancelled')
                elif pOrder.OrderStatus in (utype.THOST_FTDC_OST_PartTradedQueueing,
                        utype.THOST_FTDC_OST_PartTradedNotQueueing,
                        utype.THOST_FTDC_OST_NoTradeQueueing,
                        utype.THOST_FTDC_OST_NoTradeNotQueueing):
                    # order is partially traded
                    try:
                        self.callobj.onOrderPartialTrade(pOrder)
                    except Exception:
                        self.logger.exception('onOrderPartialTrade')
                elif pOrder.OrderStatus in (utype.THOST_FTDC_OST_AllTraded,):
                    try:
                        self.callobj.onOrderFullyTrade(pOrder)
                    except Exception:
                        self.logger.exception('onOrderFullyTrade')
                else:
                    self.logging.warning('unknown order %s status: %s'
                            %(str(oreftp), pOrder.OrderStatus))
            self.orderman.updateorder(pOrder, oreftp)
        return

    def OnRtnTrade(self, pTrade):
        '''
        成交通知
        '''
        oreftp = self.makeoreftp(pTrade.OrderRef)
        if self.orderman.ismysession(oreftp):
            try:
                callobj = self.oreftp2obj[oreftp]
            except KeyError:
                self.logging.warning('oreftp (%s) is not recored.' % str(oreftp))
            if callobj is not None:
                # pTrade has not OrderStatus field and this callback
                # is totally dedicated to notice on traded (volume, price)
                # TODO: change (simplify) orderman storing field, use this
                # callback to record 'trades'
                pass
            self.orderman.updateorder(pTrade, oreftp)
        return

    def OnRspOrderAction(self, pOrderAction, pRspInfo, nRequestID, bIsLast):
        '''
            ctp撤单校验错误
        '''
        oreftp = self.makeoreftp(pOrderAction.OrderRef)
        if self.orderman.ismysession(oreftp):
            try:
                callobj = self.oreftp2obj[oreftp]
            except KeyError:
                self.logging.warning('oreftp (%s) is not recored.' % str(oreftp))
            if callobj is not None:
                try:
                    callobj.onOrderCancelErr(pOrderAction)
                except Exception:
                    self.logger.exception('onOrderCancelErr')
            self.orderman.updateorder(pOrderAction, oreftp)
        return


    def OnErrRtnOrderAction(self, pOrderAction, pRspInfo):
        '''
            交易所撤单操作错误回报
            正常情况后不应该出现
        '''
        oreftp = self.makeoreftp(pOrderAction.OrderRef)
        if self.orderman.ismysession(oreftp):
            try:
                callobj = self.oreftp2obj[oreftp]
            except KeyError:
                self.logging.warning('oreftp (%s) is not recored.' % str(oreftp))
            if callobj is not None:
                try:
                    callobj.onOrderCancelErr(pOrderAction)
                except Exception:
                    self.logger.exception('onOrderCancelErr')
            self.orderman.updateorder(pOrderAction, oreftp)
        return

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
    1. provide interface for access order, trade, ptf, etc.
    2. order recovery on startup
    '''
    def __init__(self, omcfg):
        # oref is a tuple of (frontid, sessionid, orderref)
        self.omcfg = omcfg

        self.oreftp2oid = {}
        self.oreflock = Lock()

        # saved order field, read from config
        self.sof = set()

        # lookup cache by oreftp, actually only use front and session
        self.alloreftp = set()

    def setup(self):
        # setup connection to store server, i.e., db, redis, mongodb, etc.
        self.orderdb = redis.Redis(
                host=self.omcfg.redishost,
                port=self.omcfg.redisport,
                db=self.omcfg.odb
                )

        # TODO: build alloreftp and other caches
        return True

    def close(self):
        # close connection to store server
        self.orderdb.bgsave()

    def ismysession(oreftp):
        # oreftp as (front, session, oref)
        return ((oreftp[0], oreftp[1]) in self.alloreftp)

    def addlogin(frontid, sessionid, date):
        # get today's previous sessionid and frontid from redis
        # append this session in db for order booking and exporting.
        # return two list: session ids and fromids for date
        frontidkey = ':'.join(fdef.FRONTIDKB, date)
        sessionidkey = ':'.join(fdef.SESSIONIDKB, date)

        self.orderdb.rpush(frontidkey, frontid)
        self.orderdb.rpush(sessionidkey, sessionid)
        frontids = [int(x) for x in self.orderdb.lrange(frontidkey, 0, -1)]
        sessionids = [int(x) for x in self.orderdb.lrange(sessionidkey, 0, -1)]
        self.alloreftp = zip(frontids, sessionids)
        return frontids, sessionids

    def getoid(self, oreftp):
        oid = None
        try:
            self.oreflock.acquire()
            try:
                oid = self.oreftp2oid[oreftp]
            except KeyError:
                pass
        finally:
            self.oreflock.release()
        return oid

    def getorder(self, oreftp):
        # oreftp is a tuple of (frontid, sessionid, orderref)
        oid = self.getoid(oreftp)
        if oid is not None:
            # NOTE: redis store everything in string, so the returned
            # order dict may be different in fields types.
            return self.orderdb.hgetall(oid)

    def updateorder(self, oreftp, order):
        try:
            self.oreflock.acquire()
            if oreftp in self.oreftp2oid:
                oid = self.oreftp2oid[oref]
            else:
                # new order, create new oid and save
                # TODO: define better oid
                oid = ':'.join(fdef.ORDERNS, uuid.uuid1().hex)
                self.oreftp2oid[oreftp] = oid
        finally:
            self.oreflock.release()

        update = dict( [(k,order.__dict__[k]) for k in (self.sof & set(order.__dict__.keys()))] )
        self.orderdb.hmset(oid, update)
        return oid

    def insertorder(self, oreftp, prid, strat):
        # insert order's key IDs in db
        pass


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

