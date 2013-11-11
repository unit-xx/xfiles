#-*- coding:utf-8 -*-

import sys

import logging
import Queue
from threading import Thread, currentThread, Lock, Event
from datetime import datetime
import uuid
import cPickle as pickle
from collections import defaultdict

from MdApi import MdApi, MdSpi
from TraderApi import TraderApi, TraderSpi  
import UserApiStruct as ustruct
import UserApiType as utype

import redis

import flaredef as fdef

THOST_TERT_RESTART  = 0
THOST_TERT_RESUME   = 1
THOST_TERT_QUICK    = 2

class qrepo(MdSpi):
    '''
    Publish and store quotes in realtime.

    Currently implementation:
    - Publish in redis
    - store in memory.
    '''
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
        self.rediscfg = rediscfg
        self.reqid = 1

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
        self.repo.publish(self.qchannel, pickle.dumps(qq))
        with self.qlock:
            self.quote[q.InstrumentID] = qq

    def getquote(self, inst):
        ret = None
        with self.qlock:
            try:
                ret = self.quote[inst]
            except KeyError:
                pass
        return ret

    def setup(self):
        # don't need to store mdapi, after calling
        # RegisterSpi, we have .api attribute automatically
        self.repo = redis.Redis(
                host=self.rediscfg.host,
                port=self.rediscfg.port,
                db=self.rediscfg.repodb
                )
        self.qchannel = self.rediscfg.qchannel

        mdapi = MdApi.CreateMdApi(self.name)
        mdapi.RegisterSpi(self)
        mdapi.RegisterFront(self.mdcfg.port)
        mdapi.Init()
        return True

    def stop(self):
        self.api.Release()

class engine(TraderSpi):
    '''
    Execution engine handles orders, cancels, etc.
    '''
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

        # task queue
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

        # get strats object from name
        self.oreftp2strat = {}
        self.strats = {}
        self.stratlk = Lock()

        # mysession a tuple of (front, session)
        # so that we can filter out orders from other clients
        # and is stored in redis (by orderman) in two list
        self.mysession = None

    # helpers
    def isRspSuccess(self, RspInfo):
        return RspInfo is None or RspInfo.ErrorID == 0

    def ismysession(self, oreftp):
        return ((oreftp[0], oreftp[1]) == self.mysession)

    # from stratname to strat object
    def regstrat(self, stratname, stratobj):
        with self.stratlk:
            self.strats[stratname] = stratobj

        self.logger.info('reg strats: %s => %s' % 
                (stratname, stratobj.__class__.__name__))

    # from oreftp to stratname
    def mapstrat(self, oreftp, stratname):
        with self.stratlk:
            self.oreftp2strat[oreftp] = stratname

    # from oreftp or stratname to stratobj
    def getstrat(self, someid, by='oreftp'):
        ret = None
        stratname = None

        if by == 'oreftp':
            try:
                with self.stratlk:
                    stratname = self.oreftp2strat[someid]
            except KeyError:
                pass
        elif by == 'name':
            stratname = someid

        if stratname is not None:
            try:
                with self.stratlk:
                    ret = self.strats[stratname]
            except KeyError:
                pass
        return ret

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
        self.logger.info('req login')

    def OnRspUserLogin(self, userlogin, info, rid, is_last):
        self.logger.info(u'trader login, info:%s, rid:%s, is_last:%s' % (info, rid, is_last))
        if self.isRspSuccess(info):
            self.logger.info(u'TD:trader login success, session: %s, front: %s' % (userlogin.SessionID, userlogin.FrontID))
            self.frontid = userlogin.FrontID
            self.sessionid = userlogin.SessionID
            self.oref = int(userlogin.MaxOrderRef)
            self.islogin = True
        else:
            self.logger.warning(u'trader login failed')
            self.islogin = False
        self.loginevent.set()

    def setup(self):
        # start thread pool
        # start ctp api
        trader = TraderApi.CreateTraderApi(self.name)
        trader.RegisterSpi(self)
        trader.SubscribePublicTopic(THOST_TERT_QUICK)
        trader.SubscribePrivateTopic(THOST_TERT_QUICK)
        trader.RegisterFront(self.tradercfg.port)
        trader.Init()
        self.loginevent.wait()

        if self.islogin:
            self.orderman.addlogin(self.frontid,
                    self.sessionid, self.api.GetTradingDay())
            self.mysession = (self.frontid, self.sessionid)

        return self.islogin

    def stop(self):
        # stop ctp api
        # self.api.Release()
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

    def makeoreftp(self, order):
        # oref tuple for current session
        return (order.FrontID, order.SessionID, int(order.OrderRef))

    def myoreftp(self, oref):
        return (self.frontid, self.sessionid, oref)

    # orders and trades
    def doorder(self, inst, openclose, price, volume,
            prid=None, strat=None, ismktprice=False, isIOC=False):
        # minus volume as short

        oref = self.inc_order_ref()
        # then we submit order
        req = ustruct.InputOrder(
                InstrumentID = inst,
                Direction = utype.THOST_FTDC_D_Buy if (volume>0) else utype.THOST_FTDC_D_Sell,
                OrderRef = str(oref),
                LimitPrice = 0.0 if ismktprice else price,
                VolumeTotalOriginal = volume if (volume>0) else -volume,
                OrderPriceType = utype.THOST_FTDC_OPT_AnyPrice if ismktprice else utype.THOST_FTDC_OPT_LimitPrice,
                BrokerID = self.broker_id,
                InvestorID = self.investor_id,
                CombOffsetFlag = utype.THOST_FTDC_OF_Open if (openclose=='open') else utype.THOST_FTDC_OF_Close,
                CombHedgeFlag = utype.THOST_FTDC_HF_Speculation,
                VolumeCondition = utype.THOST_FTDC_VC_AV,
                MinVolume = 1,
                ForceCloseReason = utype.THOST_FTDC_FCC_NotForceClose,
                IsAutoSuspend = 1, # 1 or 0?
                #UserForceClose = 0, not a field in doc, a obsoleted parameter?
                TimeCondition = utype.THOST_FTDC_TC_IOC if isIOC else utype.THOST_FTDC_TC_GFD,
            )
        r = self.api.ReqOrderInsert(req, self.inc_request_id())

        # save order by orderman
        oreftp = self.myoreftp(oref)
        self.mapstrat(oreftp, strat)
        oid = self.orderman.insertorder(oreftp, prid, strat)
        self.orderman.updateorder(oid, self.transorder(req))

        # logging may hurt performance
        self.logger.info(u'下单: instrument=%s,openclose=%s,amount=%d,price=%0.3f,ismktprice=%s,isIOC=%s,OrderRef=%d,oid=%s'
                % (inst, openclose,
                    volume, price, str(ismktprice), isIOC, oref, oid))

        return r, oid

    def multiorder(self, inst, openclose, price, volume,
            prid=None, strat=None, ismktprice=False, isIOC=False):
        # minus volume as short
        # all arguments are arrays in correspondant orders
        pass

    def transorder(self, order):
        # translate a ctp inputorder object to a flare order dict
        ret = {}
        ret['inst'] = order.InstrumentID
        ret['direction'] = 'buy' if order.Direction==utype.THOST_FTDC_D_Buy else 'sell'
        ret['openclose'] = 'open' if order.CombOffsetFlag==utype.THOST_FTDC_OF_Open else 'close'
        ret['price'] = order.LimitPrice
        ret['volume'] = order.VolumeTotalOriginal
        ret['ismktprice'] = 1 if order.OrderPriceType==utype.THOST_FTDC_OPT_AnyPrice else 0
        ret['isioc'] = 1 if order.TimeCondition==utype.THOST_FTDC_TC_IOC else 0
        ret['orderref'] = order.OrderRef
        # using data from self is intended for frontid and sessionid
        ret['frontid'] = self.frontid
        ret['sessionid'] = self.sessionid
        # ExchangeID and OrderSysID is not available when calling the function.

        return ret

    def OnRspOrderInsert(self, pInputOrder, pRspInfo, nRequestID, bIsLast):
        '''
            报单未通过参数校验,被CTP拒绝
            正常情况后不应该出现
        '''
        self.logger.info('OnRspOrderInsert')
        if pInputOrder is None or pRspInfo is None:
            return

        oreftp = self.makeoreftp(pInputOrder)
        if self.ismysession(oreftp):
            oid = self.orderman.getoid(oreftp)
            self.orderman.updateorder(oid, pRspInfo, ['ErrorID', 'ErrorMsg'])

            callobj = self.getstrat(oreftp)

            if callobj is not None:
                try:
                    callobj.onOrderInsertErr(oid)
                except Exception:
                    self.logger.exception('onOrderInsertErr')
            else:
                self.logger.warning('oreftp (%s) has no mom.' % str(oreftp))
        return

    def OnErrRtnOrderInsert(self, pInputOrder, pRspInfo):
        '''
            交易所报单录入错误回报
            正常情况后不应该出现
            这个回报没有request_id
        '''
        self.logger.info('OnErrRtnOrderInsert')
        if pInputOrder is None or pRspInfo is None:
            return

        oreftp = self.makeoreftp(pInputOrder)
        if self.ismysession(oreftp):
            oid = self.orderman.getoid(oreftp)
            self.orderman.updateorder(oid, pRspInfo, ['ErrorID', 'ErrorMsg'])

            callobj = self.getstrat(oreftp)

            if callobj is not None:
                try:
                    callobj.onOrderInsertErr(oid)
                except Exception:
                    self.logger.exception('onOrderInsertErr')
            else:
                self.logger.warning('oreftp (%s) has no mom.' % str(oreftp))
        return

    def OnRtnOrder(self, pOrder):
        ''' 报单通知
            CTP、交易所接受报单
            Agent中不区分，所得信息只用于撤单
        '''
        # TODO: which state indicates partial cancel?
        if pOrder is None:
            return

        oreftp = self.makeoreftp(pOrder)
        if self.ismysession(oreftp):
            oid = self.orderman.getoid(oreftp)
            self.orderman.updateorder(oid, pOrder, ['OrderStatus', 'StatusMsg', 'OrderSubmitStatus'])

            callobj = self.getstrat(oreftp)

            if callobj is not None:
                if pOrder.OrderStatus in (utype.THOST_FTDC_OST_Unknown,
                        utype.THOST_FTDC_OST_NotTouched,
                        utype.THOST_FTDC_OST_NoTradeQueueing,
                        utype.THOST_FTDC_OST_NoTradeNotQueueing):
                    # accepted by ctp or exchange
                    if pOrder.OrderSysID!='' and pOrder.ExchangeID!='':
                        # it's a special order update here
                        self.orderman.updateidmap(oid, (pOrder.ExchangeID, pOrder.OrderSysID), by='exchid')
                        # TODO: when to update exchid map
                    try:
                        callobj.onOrderAccepted(oid)
                    except Exception:
                        self.logger.exception('onOrderAccepted')
                elif pOrder.OrderStatus in (utype.THOST_FTDC_OST_Canceled,):
                    # order is cancelled
                    try:
                        callobj.onOrderCancelled(oid)
                    except Exception:
                        self.logger.exception('onOrderCancelled')
                elif pOrder.OrderStatus in (utype.THOST_FTDC_OST_PartTradedQueueing, utype.THOST_FTDC_OST_PartTradedNotQueueing,):
                    # order is partially traded
                    try:
                        callobj.onOrderPartialTrade(oid)
                    except Exception:
                        self.logger.exception('onOrderPartialTrade')
                elif pOrder.OrderStatus in (utype.THOST_FTDC_OST_AllTraded,):
                    try:
                        callobj.onOrderFullyTrade(oid)
                    except Exception:
                        self.logger.exception('onOrderFullyTrade')
                else:
                    self.logger.warning('unknown order %s status: %s'
                            %(str(oreftp), pOrder.OrderStatus))
            else:
                self.logger.warning('oreftp (%s) has no mom.' % str(oreftp))
                
        return

    def OnRtnTrade(self, pTrade):
        '''
        成交通知
        '''
        if pTrade is None:
            self.logger.info('but without info')
            return

        exchid = (pTrade.ExchangeID, pTrade.OrderSysID)
        oid = self.orderman.getoid(exchid, 'exchid')
        if oid is None:
            self.logger.info('but no oid')
            return

        self.orderman.addtrade(oid, pTrade.Price, pTrade.Volume)

        order, olk = self.orderman.getorder(oid)
        with olk:
            stratname = order['_strat']

        callobj = self.getstrat(stratname, by='name')

        if callobj is not None:
            try:
                callobj.onOrderTrade(oid, pTrade.Price, pTrade.Volume)
            except Exception:
                self.logger.exception('onOrderInsertErr')
        else:
            self.logger.warning('oreftp (%s) has no mom.' % str(oreftp))
        return

    def OnRspOrderAction(self, pOrderAction, pRspInfo, nRequestID, bIsLast):
        '''
            ctp撤单校验错误
        '''
        if pOrderAction is None or pRspInfo is None:
            return

        oreftp = self.makeoreftp(pOrderAction)
        if self.ismysession(oreftp):
            oid = self.orderman.getoid(oreftp)
            self.orderman.updateorder(oid, pRspInfo, ['ErrorID', 'ErrorMsg'])
            self.orderman.updateorder(oid, pRspInfo, ['OrderActionStatus', 'StatusMsg'])

            callobj = self.getstrat(oreftp)

            if callobj is not None:
                try:
                    callobj.onOrderCancelErr(oid)
                except Exception:
                    self.logger.exception('onOrderCancelErr')
            else:
                self.logger.warning('oreftp (%s) has no mom.' % str(oreftp))
        return


    def OnErrRtnOrderAction(self, pOrderAction, pRspInfo):
        '''
            交易所撤单操作错误回报
            正常情况后不应该出现
        '''
        if pOrderAction is None or pRspInfo is None:
            return

        oreftp = self.makeoreftp(pOrderAction)
        if self.ismysession(oreftp):
            oid = self.orderman.getoid(oreftp)
            self.orderman.updateorder(oid, pRspInfo, ['ErrorID', 'ErrorMsg'])
            self.orderman.updateorder(oid, pRspInfo, ['OrderActionStatus', 'StatusMsg'])

            callobj = self.getstrat(oreftp)

            if callobj is not None:
                try:
                    callobj.onOrderCancelErr(oid)
                except Exception:
                    self.logger.exception('onOrderCancelErr')
            else:
                self.logger.warning('oreftp (%s) has no mom.' % str(oreftp))
        return

class engine_worker(Thread):
    '''
    Worker executes orders in async mode.
    '''
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
    1. provide interface for read/write session, order, trade, ptf, etc.
    2. order recovery on startup
    '''
    def __init__(self, omcfg):
        self.omcfg = omcfg

        # cc for cache
        self.ordercc = defaultdict(dict)
        # blk (big lock) for read/write items in ordercc
        # orderlk stores a lock for each order
        self.orderlk = defaultdict(Lock)
        self.orderblk = Lock()

        # tradecc and its lock schema is similar with ordercc
        self.tradecc = defaultdict(list)
        self.tradelk = defaultdict(Lock)
        self.tradeblk = Lock()

        # auxiliary mapping. from oreftp/exchid to oid.
        self.oreftp2oid = {}
        self.exchid2oid = {}
        self.maplk = Lock()

        # lookup cache by oreftp, actually only use front and session
        self.alloreftp = set()

        self.logger = logging.getLogger()

    def setup(self):
        # setup connection to store server, i.e., db, redis, mongodb, etc.
        self.orderdb = redis.Redis(
                host=self.omcfg.host,
                port=self.omcfg.port,
                db=self.omcfg.accountdb
                )

        # TODO: build alloreftp and other caches
        return True

    def stop(self):
        # close connection to store server
        #self.orderdb.bgsave()
        pass

    def addlogin(self, frontid, sessionid, date):
        # append new session in db for order booking and exporting.
        # don't need lock, redis will take care of atomicy.
        frontidkey = ':'.join((fdef.FRONTIDKB, date))
        sessionidkey = ':'.join((fdef.SESSIONIDKB, date))

        self.orderdb.rpush(frontidkey, frontid)
        self.orderdb.rpush(sessionidkey, sessionid)

    def getlogins(self, date):
        frontidkey = ':'.join((fdef.FRONTIDKB, date))
        sessionidkey = ':'.join((fdef.SESSIONIDKB, date))

        frontids = [int(x) for x in self.orderdb.lrange(frontidkey, 0, -1)]
        sessionids = [int(x) for x in self.orderdb.lrange(sessionidkey, 0, -1)]
        return frontids, sessionids

    # orders
    def getoid(self, someid, by='oreftp'):
        oid = None
        with self.maplk:
            try:
                if by == 'oreftp':
                    oid = self.oreftp2oid[someid]
                elif by == 'exchid':
                    self.logger.info(self.exchid2oid)
                    oid = self.exchid2oid[someid]
            except KeyError:
                pass
        return oid

    def updateidmap(self, oid, someid, by='exchid'):
        with self.maplk:
            if by=='exchid':
                self.exchid2oid[someid] = oid
            elif by=='oreftp':
                self.oreftp2oid[someid] = oid

    def getorder(self, oid):
        #return self.orderdb.hgetall(oid)
        o = None
        olk = None
        with self.orderblk:
            try:
                o = self.ordercc[oid]
                olk = self.orderlk[oid]
            except KeyError:
                pass
        return  o, olk

    def updateorder(self, oid, inorder, field=None):
        # update order with oid, using input inorder and field
        o, olk = self.getorder(oid)
        if o is not None:
            if field is None:
                toupdate = inorder
            else:
                # assume inorder is a CTP response object
                toupdate = dict( [(k,getattr(inorder, k)) for k in field] )

            #self.orderdb.hmset(oid, update)
            with olk:
                o.update(toupdate)

    def insertorder(self, oreftp, prid=None, strat=None):
        # insert order in ordercc, tradecc and updates its metadata
        ret = False

        oid = self.getoid(oreftp)
        if oid is None: # non-exist order
            ret = True
            oid = ':'.join((fdef.ORDERNS, uuid.uuid1().hex))

            olk = Lock()
            o = {}
            with self.orderblk:
                self.ordercc[oid] = o
                self.orderlk[oid] = olk

            # also insert order's trade
            tlk = Lock()
            t = []
            with self.tradeblk:
                self.tradecc[oid] = t
                self.tradelk[oid] = tlk

            with olk:
                o['_prid'] = prid
                o['_strat'] = strat

            self.updateidmap(oid, oreftp, by='oreftp')

        return oid

    def gettrade(self, oid):
        t = None
        tlk = None
        with self.tradeblk:
            try:
                t = self.tradecc[oid]
                tlk = self.tradelk[oid]
            except KeyError:
                pass
        return t, tlk

    def addtrade(self, oid, price, volume):
        ret = False
        t, tlk = self.gettrade(oid)
        if t is not None:
            ret = True
            with tlk:
                t.append((price, volume))
        return ret

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

