#-*- coding:utf-8 -*-

# flare library in message passing style.
# flame = flare in message

import logging
import cPickle as pickle
from Queue import Queue
from collections import defaultdict
from copy import deepcopy

import redis

from MdApi import MdApi, MdSpi
from TraderApi import TraderApi, TraderSpi  
import UserApiStruct as ustruct
import UserApiType as utype

from util import Record

# TODO: thread safe checking.
# TODO: exception checking.

# STATUS: code ready.
class redispubsub:
    def __init__(self, rconfig):
        self.rconfig = rconfig
        self.pubsub = None
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

# KVstore and PubSub is the impost important infrastructure.
KVstore = redis.Redis
PubSub = redispubsub

# STATUS: code ready
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
        self.pubsub = pubsub
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

class Engine(Thread):
    '''
    Engine is a router for CTP orders. It
    1. receives request from strats, and send the request to CTP
    2. receives response from CTP and send back to strats
    3. (dropped) maintains Tbook at request/order level, while the
    portfolio semantic is maintained by strats.

    Engnine communicate with strats using pubsub queue.

    Engine should be stateless on order states. It only maintains maps which
    enables routing requests and responses, e.g., CTP ID to oid, oid to
    stratname

    Engine works as a separate thread or process.

    Engine can be extended to routing orders to more than one
    account.
    '''
    def __init__(self, tradercfg, pubsub, store):
        Thread.__init__(self)

        self.broker_id = tradercfg.broker_id
        self.investor_id = tradercfg.investor_id
        self.passwd = tradercfg.passwd
        self.tradercfg = tradercfg
        self.pubsub = pubsub
        self.store = store
        self.trader = None
        self.runflag = True

        self.logger = logging.getLogger()
        self.name = self.__class__.__name__

        self.islogin = False
        self.loginevent = Event()
        self.loginevent.clear()

        self.reqid = 1
        self.reqlock = Lock()

        self.frontid = 0
        self.sessionid = 0
        self.oref = 0
        self.loginsession = ()

        # locks for increase OrderRef and RequestID
        self.oreflock = Lock()
        self.reqlock = Lock()


        # strat => (many) oid => (one) oreftp/exchid
        # reverse map from exchangeID/OrderRef to oid
        self.exch2oid = {}
        self.oref2oid = {}
        self.idmaplock = Lock()

        # map from oid to strat name
        self.oid2strat = {}
        self.stratlock = Lock()

    # threading routines.

    def run(self):
        # TODO: exception handling
        if not self.setup():
            self.logger.warning('Engine setup failed.')
            self.close()
            return

        self.logger.info('Engine setup ok.')
        while self.runflag:
            # get one order and make it
            m = self.pubsub.listen()
            # TODO: check m type and channel
            try:
                req = pickle.loads(m.data)
                self.reqorder(req)
            except Exception:
                pass
        self.close()

    def setup(self):
        # start thread pool
        # start ctp api
        # TODO: ctp settlement.
        # TODO: Engine restart and recovery.
        trader = TraderApi.CreateTraderApi(self.name)
        trader.RegisterSpi(self)
        trader.SubscribePublicTopic(THOST_TERT_QUICK)
        trader.SubscribePrivateTopic(THOST_TERT_QUICK)
        trader.RegisterFront(self.tradercfg.port)
        trader.Init()
        self.trader = trader
        self.loginevent.wait()

        if self.islogin:
            self.loginsession = (self.frontid, self.sessionid)
            # TODO: check orderchannel
            self.pubsub.subscribe(orderchannel)

        return self.islogin

    def close(self):
        if self.trader:
            self.trader.Release()
            self.trader = None

    def stop(self):
        self.runflag = False

    # Request and helpers.

    def makereq(self, req):
        '''
        Send CTP request. 
        req is a Record object.

        Required fields:
        oid, strat,
        inst, volume(minus for sell), price(-1 for mkt price), openclose

        Optional:
        FAK, FOK, etc.
        '''
        # make ctp request
        # update reverse map
        # and submit
        oref = self.inc_order_ref()
        ismktprice = True if req.price<0 else False

        ctpreq = ustruct.InputOrder(
                InstrumentID = req.inst,
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
        # NOTE: what if ReqOrderInsert return false?
        r = self.api.ReqOrderInsert(ctpreq, self.inc_request_id())

        # save order by orderman
        oreftp = self.myoreftp(oref)
        oid = req.oid
        strat = req.strat

        self.setoidmap(oid, oreftp)
        self.setstratmap(oid, strat)

        # logging may hurt performance
        #self.logger.info(u'下单: instrument=%s,openclose=%s,amount=%d,price=%0.3f,ismktprice=%s,isIOC=%s,OrderRef=%d,oid=%s'
        #        % (inst, openclose,
        #            volume, price, str(ismktprice), isIOC, oref, oid))

        return

    def setoidmap(self, oid, someid, by='oref'):
        '''
        update reverse map oreftp/exchid => oid
        '''
        with self.idmaplock:
            if by=='exchid':
                self.exch2oid[someid] = oid
            elif by=='oref':
                self.oref2oid[someid] = oid

    def getoid(self, someid, type='oref'):
        '''
        get oid by oref/exchid
        '''
        oid = None
        with self.idmaplock:
            try:
                if by == 'oref':
                    oid = self.oref2oid[someid]
                elif by == 'exchid':
                    #self.logger.info(self.exchid2oid)
                    oid = self.exch2oid[someid]
            except KeyError:
                pass
        return oid

    def setstratmap(self, oid, strat):
        '''
        update map oid => stratname
        '''
        with self.stratlock:
            self.oid2strat[oid] = strat

    def getstrat(self, oid):
        strat = None
        with self.stratlock:
            try:
                strat = self.oid2strat[oid]
            except KeyError:
                pass
        return strat

    def ismysession(self, oreftp)
        # use oref or order?
        ret = False
        if self.islogin:
            ret = ((oreftp[0], oreftp[1]) == self.mysession)
        return ret

    def myoreftp(self, oref):
        return (self.frontid, self.sessionid, oref)

    def makeoreftp(self, order):
        # oref tuple for current session
        return (order.FrontID, order.SessionID, int(order.OrderRef))

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

    # Response handlers for login.

    def isRspSuccess(self, RspInfo):
        return RspInfo is None or RspInfo.ErrorID == 0

    def OnFrontDisConnected(self, reason):
        self.logger.info(u'Engine disconnected, reason:%s' % (reason,))
        self.islogin = False

    def OnFrontConnected(self):
        self.logger.info(u'Engine connected.')
        self.user_login(self.broker_id, self.investor_id, self.passwd)

    def user_login(self, broker_id, investor_id, passwd):
        req = ustruct.ReqUserLogin(BrokerID=broker_id, UserID=investor_id, Password=passwd)
        r=self.api.ReqUserLogin(req, self.inc_request_id())

    def OnRspUserLogin(self, userlogin, info, rid, is_last):
        self.logger.info(u'Engine login, info:%s, rid:%s, is_last:%s' % (info, rid, is_last))
        if self.isRspSuccess(info):
            self.logger.info(u'Engine login success, session: %s, front: %s' % (userlogin.SessionID, userlogin.FrontID))
            self.frontid = userlogin.FrontID
            self.sessionid = userlogin.SessionID
            self.oref = int(userlogin.MaxOrderRef)
            self.islogin = True
        else:
            self.logger.warning(u'Engine login failed')
            self.islogin = False
        self.loginevent.set()

    # Handlers for order response.
    # These handlers just publish responses in pubsub, while strats handlers,
    # orderman, tbook and monitors will do their jobs on receiving responses.

    # TODO: add settlement confirmation handlers?

    def makerecord(self, order):
        '''
        oid, strat, state, etc.
        '''
        pass

    def OnRspOrderInsert(self, pInputOrder, pRspInfo, nRequestID, bIsLast):
        '''
            报单未通过参数校验,被CTP拒绝
            正常情况后不应该出现
        '''
        # TODO: what if isRspSuccess returns False.
        if pInputOrder is None or pRspInfo is None:
            return

        oreftp = self.makeoreftp(pInputOrder)
        if self.ismysession(oreftp):
            rec = self.makerecord(pInputOrder)
            self.pubsub.publish(channel, rec)

    def OnErrRtnOrderInsert(self, pInputOrder, pRspInfo):
        '''
            交易所报单录入错误回报
            正常情况后不应该出现
            这个回报没有request_id
        '''
        pass

    def OnRtnOrder(self, pOrder):
        ''' 
            报单通知
            CTP、交易所接受报单
            Agent中不区分，所得信息只用于撤单
        '''
        pass

    def OnRtnTrade(self, pTrade):
        '''
        成交通知
        '''
        pass

    def OnRspOrderAction(self, pOrderAction, pRspInfo, nRequestID, bIsLast):
        '''
            ctp撤单校验错误
        '''
        pass

    def OnErrRtnOrderAction(self, pOrderAction, pRspInfo):
        '''
            交易所撤单操作错误回报
            正常情况后不应该出现
        '''
        pass

'''
A strategy is splitted into top and bottom parts. The top part listens for
quotes and other input data streams, then generates trading signals to engine
through pubsub. The bottom part listens for order responses from engine through
pubsub and invoke strategy callbacks.
'''
class stratbottom(Thread):
    def __init__(self):
        Thread.__init__(self, pubsub, wsize)
        self.queue = Queue.Queue()
        self.wset = []
        self.wsize = wsize
        self.pubsub = pubsub
        self.strats = {}
        self.runflag = True

    def run(self):
        # start workers
        for i in range(self.wsize):
            w = stratworker(self.queue)
            self.wsize.append(w)
            w.start()

        while self.runflag:
            t = self.pubsub.listen()
            if(self.hasstrat(t)):
                self.queue.put(t)

        self.close()

    def stop(self):
        self.runflag = False

    def close(self):
        pass

    def addstrat(self, sname, strat):
        pass

    def hasstrat(self, sname):
        pass

    def getstrat(self, sname):
        pass

    def handleOpenResp(self):
        if resp=='ok':
            self.pubsub.publish(Tbook, Update, oid)
            self.pubsub.publish(Tbook, Confirm, oid)
        elif resp=='error':
            self.pubsub.publish(Tbook, Update, oid)
            self.pubsub.publish(Tbook, Release, oid)

    def handleCloseResp(self):
        pass

    def handleCancelResp(self):
        if resp=='ok':
            self.pubsub.publish(Tbook, Update, oid)
            self.pubsub.publish(Tbook, Release, oid)
        elif resp=='error':
            self.pubsub.publish(Tbook, Update, oid)

class stratworker(Thread):
    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue
        self.runflag = True

    def run(self):
        while self.runflag:
            try:
                t = self.queue.get(True, 2)
                self.process(t)
            except Queue.Empty:
                pass

    def stop(self):
        self.runflag = False

    def process(self, t):
        try:
            # get strategy object
            # get t's callback
            # call strategy's corresponding callback.
            strat = self.getstrat()
            strat.handleresp(t)
        except:
            pass

# STATUS: just shows concepts.
class strattop(Thread):
    '''
    1. a defined strategy task has only one instance at any time.
    2. when a strategy task is restarted, it has to recover from previous run, including orders, positions, margins, cash account, etc.
    3. 
    '''
    def __init__(self):
        Thread.__init__(self)
        self.runflag = True
        self.logger = logging.getLogger()
        self.name = self.__class__.__name__

    def setup(self):
        pass

    def signal(self):
        # listen for input streams and generate trading signals, or
        # call stop() to quit strategy.
        pass

    def run(self):
        try:
            if False == self.setup():
                return
        except:
            return

        while self.runflag:
            self.signal()

    def stop(self):
        self.runflag = False

class TBookCache:
    '''
    TBookCache has the similar interface with TBookLib, but it caches updates in
    memory. It may also queues updates to TBookProxy for persistence.
    '''
    def __init__(self, tbproxy=None):
        self.qproxy = tbproxy.getqueue()
        self.tbproxy = tbproxy

        # cc for cache
        # ordercc is mapped to redis directly.
        self.ordercc = defaultdict(dict)
        # blk (big lock) for read/write items in ordercc
        # orderlk stores a lock for each order
        self.orderlk = defaultdict(Lock)
        self.orderblk = Lock()

        # tradecc and its lock schema is similar with ordercc
        # tradecc can be mapped to redis as pickled string
        self.tradecc = defaultdict(list)
        self.tradelk = defaultdict(Lock)
        self.tradeblk = Lock()

        # ptf cache
        # a ptf instance is a list of dict, it can be mapped to redis as
        # pickled string.
        self.ptfinstcc = defaultdict(list)
        self.ptfdefcc = defaultdict(list)
        self.ptfblk = Lock()

        self.logger = logging.getLogger()

    def getorder(self, oid):
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
                # assume inorder is a Record object
                toupdate = dict( [(k, inorder[k])) for k in field] )
            with olk:
                o.update(toupdate)

    def hasorder(self, oid):
        ret = False
        with self.orderblk:
            if oid in self.ordercc:
                ret = True
        return ret

    def neworder(self, oid):
        # insert order in ordercc, tradecc and updates its metadata
        ret = False

        if not self.hasorder(oid):
            ret = True
            oidlocal = fdef.localoid()
            oid = fdef.makename(fdef.ORDERNS, oidlocal)

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

        return ret

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

    def loadptfdef(self, ptfdefid):
        ret = False
        pdef = self.tbproxy.getptfdef(ptfdefid)
        if pdef is not None:
            ret = True
            with self.ptfblk:
                self.ptfdefcc[ptfdefid] = pdef

        return ret

    def newptf(self, ptfdefid):
        '''
        ptfdef is a list of dict, or to say several rows.
        Keys are defined in flaredef, and they are:
        code, shares(minus for short), and tag.

        A ptf instance is a ptfdef with oid for each code... :)

        like neworder, insert records in ptfinstcc, add oid, insert new orders,
        and return ptfid
        '''
        return None

    def getptf(self, ptfid):
        '''
        like getorder
        '''
        pass

class TBookProxy(Thread):
    '''
    Receive queueed Tbook updates and 1. store updates in redis using TBookLib, 2. breadcasts update through pubsub.
    '''
    def __init__(self, pubsub, store):
        Thread.__init__(self)
        self.pubsub = pubsub
        self.store = store
        self.tb = TBookLib()
        self.queue = Queue()
        self.runflag = True

    def run(self):
        while self.runflag:
            try:
                br = self.queue.get(True, 2)
                self.process(br)
                self.queue.task_done()
            except Queue.Empty:
                pass

    def stop(self):
        self.runflag = False

    def process(self, br):
        try:
            self.tb.update(self.store, br)
            self.pubsub.publish(br)
        except:
            pass

    def getqueue(self):
        return self.queue

    def getptfdef(self, ptfdefid):
        ret = self.tb.getptfdef(ptfdefid)
        return ret

class TBookLib:
    '''
    TBookLib APIs are invoked to update orders/trades, etc. to redis.

    --(invoke)-->TBook API--(redis api)-->redis
    '''
    def update(self, store, t):
        # update t in store

    def getptfdef(self, ptfdefid):
        return None
