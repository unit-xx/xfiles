#-*- coding:utf-8 -*-

# flare library in message passing style.
# flame = flare in message

import logging
import cPickle as pickle
from Queue import Queue, Empty
from collections import defaultdict
from copy import deepcopy
import cPickle as pickle
from threading import Thread, Lock, Event

import redis

from MdApi import MdApi, MdSpi
from TraderApi import TraderApi, TraderSpi  
import UserApiStruct as ustruct
import UserApiType as utype

from util import Record
import flaredef as fdef

THOST_TERT_RESTART = 0
THOST_TERT_RESUME = 1
THOST_TERT_QUICK = 2
# TODO: thread safe checking.
# TODO: exception checking.

# STATUS: code ready.
class redispubsub:
    def __init__(self, rconfig):
        self.rconfig = rconfig
        self.pubsub = None
        self.redis = None

    def setup(self):
        self.redis = redis.Redis(**self.rconfig)
        self.pubsub = self.redis.pubsub()

    def publish(self, channel, msg):
        self.redis.publish(channel, msg)

    def subscribe(self, channel):
        self.pubsub.subscribe(channel)

    def unsubscribe(self, channel):
        self.pubsub.unsubscribe(channel)

    def listen(self):
        '''
        return message is a dictonary like:
        {'pattern': None, 'type': 'message', 'channel': 'xxx', 'data': '123'}
        {'pattern': None, 'type': 'subscribe', 'channel': 'xxx', 'data': 1L}
        should filter by type, pattern and channel.
        '''
        while 1:
            ret = next(self.pubsub.listen())
            if 'message' == ret['type']:
                break
        return ret

# KVstore and PubSub is the most important infrastructure.
KVstore = redis.Redis
PubSub = redispubsub

def getstore(cfg):
    '''
    cfg is a dict, like {'host': 'localhost', 'port': 1234}
    '''
    r = KVstore(**cfg)
    return r

# STATUS: code ready
class qrepo(MdSpi):
    '''
    Receive quotes from CTP and 1) publish, 2) store quotes.
    Assumed to run as a single thread.
    '''
    def __init__(self, instruments, mdconfig, pubsub, store):
        self.instruments = instruments
        self.broker_id = mdconfig['broker_id']
        self.investor_id = mdconfig['investor_id']
        self.passwd = mdconfig['passwd']
        self.mdcfg = mdconfig
        self.store = store
        self.pubsub = pubsub
        self.qchannel = fdef.CHQUOTE
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
        self.logger.info('Connected to CTP quote server.')
        self.user_login(self.broker_id, self.investor_id, self.passwd)

    def user_login(self, broker_id, investor_id, passwd):
        req = ustruct.ReqUserLogin(BrokerID=broker_id, UserID=investor_id, Password=passwd)
        r=self.api.ReqUserLogin(req, self.inc_request_id())

    def OnRspUserLogin(self, userlogin, info, rid, is_last):
        if self.isRspSuccess(info):
            if is_last:
                self.api.SubscribeMarketData(self.instruments)
                self.logger.info('subscribe quote for: %s' % self.instruments)
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
        try:
            qd = pickle.dumps(qq, -1)
            self.pubsub.publish(self.qchannel, qd)
            qkey = fdef.fullname(fdef.QUOTENS, q.InstrumentID)
            self.store.hmset(qkey, qq)
        except pickle.PickleError:
            pass

    def setup(self):
        # don't need to store mdapi, after calling
        # RegisterSpi, we have .api attribute automatically
        mdapi = MdApi.CreateMdApi(self.name)
        mdapi.RegisterSpi(self)
        mdapi.RegisterFront(self.mdcfg['port'])
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
            self.pubsub.subscribe(fdef.CHOREQ)

        return self.islogin

    def close(self):
        self.pubsub.unsubscribe(fdef.CHOREQ)
        if self.trader:
            self.trader.Release()
            self.trader = None

    def stop(self):
        self.runflag = False

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
            try:
                req = Record.load(m['data'])
                if req[fdef.KACTION] == fdef.VINSERT:
                    self.reqorder(req)
                elif req[fdef.KACTION] == fdef.VCANCEL:
                    self.cancelorder(req)
            except Exception:
                self.logger.exception('handling req error')
        self.close()

    def reqorder(self, req):
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
        code = req[fdef.KCODE]
        ismktprice = True if req[fdef.KPRICE]<0 else False
        volume = req[fdef.KVOLUME]
        price = req[fdef.KPRICE]
        otype = req[fdef.OTYPE]
        isIOC = (fdef.KISIOC in req) and req[fdef.KISIOC]

        ctpreq = ustruct.InputOrder(
                InstrumentID = code,
                Direction = utype.THOST_FTDC_D_Buy if (volume>0) else utype.THOST_FTDC_D_Sell,
                OrderRef = str(oref),
                LimitPrice = 0.0 if ismktprice else price,
                VolumeTotalOriginal = volume if (volume>0) else -volume,
                OrderPriceType = utype.THOST_FTDC_OPT_AnyPrice if ismktprice else utype.THOST_FTDC_OPT_LimitPrice,
                BrokerID = self.broker_id,
                InvestorID = self.investor_id,
                CombOffsetFlag = utype.THOST_FTDC_OF_Open if (otype==fdef.VOPEN) else utype.THOST_FTDC_OF_Close,
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
        oid = req[fdef.KOID]
        strat = req[fdef.KSTRAT]

        self.setoidmap(oid, oreftp)
        self.setstratmap(oid, strat)

        # XXX: why strat here?
        channel = fdef.fullname(fdef.CHORESP, strat)
        rec = self.makerecord(ctpreq, oid, strat,
                ['FrontID', 'SessionID', 'OrderRef'])
        rec[fdef.KOSTATE] = fdef.VORDERREQED
        self.pubsub.publish(channel, rec.dump())

        # logging may hurt performance
        #self.logger.info(u'下单: instrument=%s,openclose=%s,amount=%d,price=%0.3f,ismktprice=%s,isIOC=%s,OrderRef=%d,oid=%s'
        #        % (inst, openclose,
        #            volume, price, str(ismktprice), isIOC, oref, oid))

        return

    def cancelorder(self, req):
        code = req[fdef.KCODE]
        oref = req['OrderRef']

        ctpreq = ustruct.InputOrderAction(
                ActionFlag = utype.THOST_FTDC_AF_Delete,
                BrokerID = self.broker_id,
                InvestorID = self.investor_id,
                InstrumentID = code,
                SessionID = self.sessionid,
                FrontID = self.frontid,
                OrderRef = oref
                )
        r = self.api.ReqOrderAction(ctpreq, self.inc_request_id())

    def setoidmap(self, oid, someid, by='oref'):
        '''
        update reverse map oreftp/exchid => oid
        '''
        with self.idmaplock:
            if by=='exchid':
                self.exch2oid[someid] = oid
            elif by=='oref':
                self.oref2oid[someid] = oid

    def getoid(self, someid, by='oref'):
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

    def ismysession(self, oreftp):
        # use oref or order?
        ret = False
        if self.islogin:
            ret = ((oreftp[0], oreftp[1]) == (self.frontid, self.sessionid))
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

    def makerecord(self, ctporder, oid, strat, fields=[]):
        '''
        oid, strat, state, etc.
        '''
        ret = Record()
        ret[fdef.KOID] = oid
        ret[fdef.KSTRAT] = strat
        for k in fields:
            ret[k] = getattr(ctporder, k)

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
            oid = self.getoid(oreftp)
            strat = self.getstrat(oid)
            rec = self.makerecord(pInputOrder, oid, strat)
            rec[fdef.KOSTATE] = fdef.VORDERREJECTED
            rec.update(pRspInfo)
            channel = fdef.fullname(fdef.CHORESP, strat)

            self.pubsub.publish(channel, rec.dump())

    def OnErrRtnOrderInsert(self, pInputOrder, pRspInfo):
        '''
            交易所报单录入错误回报
            正常情况后不应该出现
            这个回报没有request_id
        '''
        if pInputOrder is None or pRspInfo is None:
            return

        oreftp = self.makeoreftp(pInputOrder)
        if self.ismysession(oreftp):
            oid = self.getoid(oreftp)
            strat = self.getstrat(oid)
            rec = self.makerecord(pInputOrder, oid, strat)
            rec.update(pRspInfo)
            rec[fdef.KOSTATE] = fdef.VORDERREJECTED
            channel = fdef.fullname(fdef.CHORESP, strat)

            self.pubsub.publish(channel, rec.dump())

    def OnRtnOrder(self, pOrder):
        ''' 
            报单通知
            CTP、交易所接受报单
            Agent中不区分，所得信息只用于撤单
        '''
        if pOrder is None:
            return

        oreftp = self.makeoreftp(pOrder)
        if self.ismysession(oreftp):
            oid = self.getoid(oreftp)
            strat = self.getstrat(oid)
            rec = self.makerecord(pOrder, oid, strat, ['OrderStatus', 'StatusMsg', 'OrderSubmitStatus', 'OrderActionStatus'])
            rec[fdef.KTRADEVOL] = pOrder.VolumeTraded
            rec[fdef.KUNTRADEVOL] = pOrder.VolumeTotal
            channel = fdef.fullname(fdef.CHORESP, strat)

            if pOrder.OrderStatus in (utype.THOST_FTDC_OST_Unknown,
                    utype.THOST_FTDC_OST_NotTouched,
                    utype.THOST_FTDC_OST_NoTradeQueueing,
                    utype.THOST_FTDC_OST_NoTradeNotQueueing):
                # accepted by ctp or exchange
                rec[fdef.KOSTATE] = fdef.VORDERACCEPTED

                if pOrder.OrderSysID!='' and pOrder.ExchangeID!='':
                    # it's a special order update here
                    # TODO: when to update exchid map
                    self.setoidmap(oid, (pOrder.ExchangeID, pOrder.OrderSysID), by='exchid')
                    rec['ExchangeID'] = pOrder.ExchangeID
                    rec['OrderSysID'] = pOrder.OrderSysID
            elif pOrder.OrderStatus in (utype.THOST_FTDC_OST_Canceled,):
                rec[fdef.KCANCELSTATE] = fdef.VCANCELLED
            elif pOrder.OrderStatus in (utype.THOST_FTDC_OST_PartTradedQueueing, utype.THOST_FTDC_OST_PartTradedNotQueueing,):
                rec[fdef.KOSTATE] = fdef.VORDERPTRADE
            elif pOrder.OrderStatus in (utype.THOST_FTDC_OST_AllTraded,):
                rec[fdef.KOSTATE] = fdef.VORDERFTRADE
            else:
                self.logger.warning('unknown order status: strat=%s, oid=%s, status=%s' %(strat, oid, pOrder.OrderStatus))

            self.pubsub.publish(channel, rec.dump())

        return

    def OnRtnTrade(self, pTrade):
        '''
        成交通知
        '''
        if pTrade is None:
            return

        exchid = (pTrade.ExchangeID, pTrade.OrderSysID)
        oid = self.getoid(exchid, 'exchid')
        if oid is None:
            self.logger.info('trade with no oid')
            return

        strat = self.getstrat(oid)
        rec = self.makerecord(pTrade, oid, strat)
        rec[fdef.KTRADESTATE] = fdef.VTRADENEW
        rec[fdef.KVOLUME] = pTrade.Volume
        rec[fdef.KPRICE] = pTrade.Price
        #rec[fdef.KCODE] = pTrade.InstrumentID
        #rec[fdef.KOTYPE] = fdef.VOPEN if (utype.THOST_FTDC_OF_Open==pTrade.OffsetFlag) else fdef.VCLOSE
        #rec[fdef.KDIR] = fdef.VLONG if (utype.THOST_FTDC_D_Buy==pTrade.Direction) else fdef.VSHORT

        channel = fdef.fullname(fdef.CHORESP, strat)

        self.pubsub.publish(channel, rec.dump())

    def OnRspOrderAction(self, pOrderAction, pRspInfo, nRequestID, bIsLast):
        '''
            ctp撤单校验错误
        '''
        if pOrderAction is None or pRspInfo is None:
            return

        oreftp = self.makeoreftp(pOrderAction)
        if self.ismysession(oreftp):
            oid = self.getoid(oreftp)
            strat = self.getstrat(oid)
            rec = self.makerecord(pOrderAction, oid, strat, ['OrderActionStatus', 'StatusMsg'])
            rec.update(pRspInfo)
            rec[fdef.KCANCELSTATE] = fdef.VCANCELREJECTED
            channel = fdef.fullname(fdef.CHORESP, strat)

            self.pubsub.publish(channel, rec.dump())

    def OnErrRtnOrderAction(self, pOrderAction, pRspInfo):
        '''
            交易所撤单操作错误回报
            正常情况后不应该出现
        '''
        if pOrderAction is None or pRspInfo is None:
            return

        oreftp = self.makeoreftp(pOrderAction)
        if self.ismysession(oreftp):
            oid = self.getoid(oreftp)
            strat = self.getstrat(oid)
            rec = self.makerecord(pOrderAction, oid, strat, ['OrderActionStatus', 'StatusMsg'])
            rec.update(pRspInfo)
            rec[fdef.KCANCELSTATE] = fdef.VCANCELREJECTED
            channel = fdef.fullname(fdef.CHORESP, strat)

            self.pubsub.publish(channel, rec.dump())

'''
A strategy is splitted into top and bottom parts. The top part listens for
quotes and other input streams, and generates trading signals. The bottom part
listens for order responses from engine and invoke strategy callbacks.
'''
class strattop(Thread):
    '''
    1. a defined strategy task has only one instance at any time.
    2. when a strategy task is restarted, it has to recover from previous run, including orders, positions, margins, cash account, etc.
    3. 
    '''
    def __init__(self, tbook):
        self.tbook = tbook

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

    def getstrat(self):
        pass

    def reqorder(self):
        '''
        neworder
        riskcheck
        reserve
        submit
        '''
        pass

    def riskcheck(self, order):
        '''
        return True for ok to submit order.
        '''
        return False

    def onOrderState(self, oid, resp):
        self.tbook.updateorder(oid, resp)
        state = resp[fdef.KOSTATE]
        if state == fdef.VORDERREJECTED:
            self.onOrderRejected(oid, resp)
        elif state == fdef.VORDERACCEPTED:
            self.onOrderAccepted(oid, resp)
        elif state == fdef.VORDERPTRADE:
            self.onOrderPartialTrade(oid, resp)
        elif state == fdef.VORDERFTRADE:
            self.OnOrderFullyTrade(oid, resp)

    def onOrderRejected(self, oid, resp):
        '''
        interface
        '''
        pass

    def onOrderAccepted(self, oid, resp):
        '''
        interface
        '''
        pass

    def onOrderPartialTrade(self, oid, resp):
        '''
        interface
        '''
        pass

    def OnOrderFullyTrade(self, oid, resp):
        '''
        interface
        '''
        pass

    def onTradeState(self, oid, resp):
        # arrive here only when new trade is informed.
        self.tbook.addtrade(oid, resp)
        self.onNewTrade(oid, resp)

    def onNewTrade(self, oid, trade):
        '''
        interface
        '''
        pass

    def onCancelState(self, oid, resp):
        self.tbook.updateorder(oid, resp)
        state = resp[fdef.KCANCELSTATE]
        if state == fdef.VCANCELREJECTED:
            self.onCancelRejected(oid, resp)
        elif state == fdef.VCANCELLED:
            self.onCancelled(oid, resp)

    def onCancelRejected(self, oid, resp):
        '''
        interface
        '''
        pass

    def onCancelled(self, oid, resp):
        '''
        interface
        '''
        pass

class stratbottom(Thread):
    def __init__(self, pubsub, top):
        Thread.__init__(self)
        self.pubsub = pubsub
        self.top = top
        self.strat = None
        self.logger = logging.getLogger()

    def run(self):
        self.strat = self.top.getstrat()
        chname = fdef.fullname(fdef.CHORESP, self.strat)
        self.pubsub.subscribe(chname)

        while self.runflag:
            t = self.pubsub.listen()
            resp = Record.load(t['data'])
            oid = resp[fdef.KOID]
            #resp.pop(fdef.KOID])
            try:
                if fdef.KOSTATE in resp.keys():
                    self.top.onOrderState(oid, resp)
                elif fdef.KTRADESTATE in resp.keys():
                    self.top.onTradeState(oid, resp)
                elif fdef.KCANCELSTATE in resp.keys():
                    self.top.onCancelState(oid, resp)
                else:
                    self.logger.error('Unknown state.')
            except:
                self.logger.exception('On handling engine response.')

    def stop(self):
        self.runflag = False

'''
class stratdispatch(Thread):
    def __init__(self):
        Thread.__init__(self)
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
'''

class TBookCache:
    '''
    TBookCache has the similar interface with TBookLib, but it caches updates
    in memory. It syncs updates updates to TBookProxy for persistence. To
    initialize cache it read data from store using TBookLib interface.

    What TBook should do and know:
    1. static balance, dynamic balance, total margins, available cash
    2. positions: code+direction: position, avg price, margins, PNL
    3. orders, trades
    4. check and update cash/margins/PNL/balance before order submission,
    after order submission(reject, accept, new trade), after cancel
    confirmatin and new quotes.
    5. daily settlement.
    '''
    def __init__(self, strat, tbproxy=None):
        self.tbproxy = tbproxy
        self.qproxy = tbproxy.getqueue()
        self.strat = strat

        self.bkname = None

        # to be updated according to linked strategy and readonly.
        self.posmax = {}

        # cc for cache
        # ordercc is mapped to redis directly.
        self.ordercc = {}
        # blk (big lock) for read/write items in ordercc
        # orderlk stores a lock for each order
        self.orderlk = {}
        self.orderblk = Lock()

        # tradecc and its lock schema is similar with ordercc
        # tradecc can be mapped to redis as pickled string
        #self.tradecc = defaultdict(list)
        #self.tradelk = defaultdict(Lock)
        #self.tradeblk = Lock()

        # postion key is a namedtuple(code, dir), value
        # is a dict recording volumes, avg price, quota etc
        self.poscc = {}
        self.poslk = {}
        self.posblk = Lock()

        # ptf cache
        # a ptf instance is a list of dict, it can be mapped to redis as
        # pickled string.
        self.ptfinstcc = {}
        self.ptfdefcc = {}
        self.ptfblk = Lock()

        self.name = self.__class__.__name__
        self.logger = logging.getLogger()

    def setup(self):
        '''
        initialize by reading from redis.

        check strat-tbook mapping
        read all orders/positions

        '''
        tblib = self.tbproxy.gettblib()
        if self.strat != tblib.strat:
            return False

        self.bkname = tblib.tbname

        # init all orders. in setup it may not need xxxblk.
        oids = tblib.getalloid()
        for oid in oids:
            order = tblib.getorder(oid)
            self.ordercc[oid] = order
            self.orderlk[oid] = Lock()

        poskeys = tblib.getallposkey()
        for poskey in poskeys:
            pos = tblib.getposition(poskey)
            self.poscc[poskey] = pos
            self.poslk[poskey] = Lock()

    def getorder(self, oid):
        o = None
        olk = None
        with self.orderblk:
            if oid in self.ordercc:
                o = self.ordercc[oid]
                olk = self.orderlk[oid]
        return  o, olk

    def updateorder(self, oid, order, field=[]):
        '''
        - update order with oid, using input order and field

        Readonly Keys after reserved/requested:

        KOID
        KSTRAT
        KACTION
        KOTYPE
        KDIR
        KCODE
        KVOLUME
        KPRICE
        KISIOC
        KISRESERVED

        KTAG?

        Mostly updated:

        KOSTATE
        KCANCELSTATE
        (ctp attributes)

        '''

        # TODO: check that only updatable keys are updated
        o, olk = self.getorder(oid)
        if o is not None:
            toupdate = { k:order[k] for k in field }
            with olk:
                o.update(toupdate)

            # update reserve if order is cancelled, and order is reserved
            if fdef.KCANCELSTATE in order and order[fdef.KISRESERVED]==True:
                otype = order[fdef.OTYPE]
                if otype == fdef.VOPEN:
                    if order[fdef.KCANCELSTATE]==fdef.VCANCELLED:
                        code = order[fdef.KCODE]
                        direction = order[fdef.KDIR]
                        # NOTE: assume that all untraded volume is cancelled.
                        untrade = order[fdef.KUNTRADEVOL]
                        poskey = fdef.genposkey(code, direction)
                        p, plk = self.getposition(poskey)
                        with plk:
                            p[fdef.KRESERVED] -= untrade

    def doreserve(self, oid):
        '''
        check risk measures and reserve order in position.
        only reserve `insert open long/short order'
        '''
        ret = False

        order, olk = self.getorder(oid)

        action = order[fdef.KACTION]
        otype = order[fdef.OTYPE]
        code = order[fdef.KCODE]
        direction = order[fdef.KDIR]
        volume = order[fdef.KVOLUME]
        if action != fdef.VINSERT or otype != fdef.VOPEN:
            return ret

        poskey = fdef.genposkey(code, direction)
        p, plk = self.getposition(poskey)
        with plk:
            if p[fdef.MAXLIMIT] >= (volume+p[fdef.KPOSITION]):
                p[fdef.KRESERVED] += volume
                ret = True

        if ret:
            with olk:
                order[fdef.KISRESERVED] = True

        return ret

    def freereserve(self, oid, count):
        '''
        Need this function?
        '''
        pass

    def hasorder(self, oid):
        ret = False
        with self.orderblk:
            if oid in self.ordercc:
                ret = True
        return ret

    def neworder(self, order):
        # insert order in ordercc, tradecc and updates its metadata
        oidlocal = fdef.localoid()
        oid = fdef.makename(fdef.ORDERNS, oidlocal)

        olk = Lock()
        o = deepcopy(order)
        with self.orderblk:
            self.ordercc[oid] = o
            self.orderlk[oid] = olk

        with olk:
            o[fdef.KOID] = oid
            o[fdef.KTRADE] = []
            o[fdef.KISRESERVED] = False
            o[fdef.KOSTATE] = fdef.VORDERINIT
            o[fdef.KCANCELSTATE] = fdef.VCANCELINIT

        return o, olk

    #def gettrade(self, oid):
    #    t = None
    #    tlk = None
    #    with self.tradeblk:
    #        try:
    #            t = self.tradecc[oid]
    #            tlk = self.tradelk[oid]
    #        except KeyError:
    #            pass
    #    return t, tlk

    def addtrade(self, oid, trade):
        # update postion, reserve, margin, etc.
        ret = False
        order, olk = self.getorder(oid)
        if order is not None:
            ret = True
            price = trade[fdef.KPRICE]
            volume = trade[fdef.KVOLUME]
            with olk:
                order[fdef.KTRADE].append((price, volume))

            # update position
            code = order[fdef.KCODE]
            direction = order[fdef.KDIR]
            otype = order[fdef.KOTYPE]
            poskey = fdef.genposkey(code, direction)
            p, plk = self.getposition(poskey)
            with plk:
                if otype == fdef.VOPEN:
                    # average trade price
                    cpos = p[fdef.KPOSITION]
                    cprice = p[fdef.KAVGPRICE]
                    p[fdef.KAVGPRICE] = (cpos*cprice + volume*price)/(cpos+volume)
                    # total position
                    p[fdef.KPOSITION] += volume
                    # reserved count
                    p[fdef.KRESERVED] -= volume
                elif otype == fdef.VCLOSE:
                    p[fdef.KPOSITION] -= volume

        return ret

    def getposition(self, poskey):
        p = None
        plk = None
        with self.posblk:
            try:
                p = self.poscc[poskey]
                plk = self.poslk[poskey]
            except KeyError:
                # Ok, a postion entry hasn't been added, but is needed.
                p = {}
                plk = Lock()
                self.poscc[poskey] = p
                self.poslk[poskey] = plk
                p[fdef.KPOSITION] = 0
                p[fdef.KRESERVED] = 0
                p[fdef.KAVGPRICE] = 0.0
                p[fdef.KMAXLIMIT] = self.posmax[poskey]

        return p, plk

    def updateposition(self, pos):
        '''
        - Margin calculation:

        init: 0
        requested: based on ordered price,
        rejected: 0
        accepted: based on ordered price,
        partial trade: ordered price + traded price
        full traded: traded price

        (cancel state implication)
        cancel init: no effect
        canceling: no effect
        canceled: only traded price
        cancel failed: no effect

        - Positions:
        contract+direction: position, reserved, trade price, margin, PNL
        '''
        pass

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
        code, volumes(minus for short), and tag.

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

class TBookLib:
    '''
    TBook talks directly with redis to read/write tbook.

    Currently a tbook is assigned to one strategy.

    --(invoke)-->TBook API--(redis api)-->redis

    NOTE: redis stores values as string.

    A TBook in redis is stored as:

    bkname (id)
    linked strat name
    orders
    trades
    positions

    A TBook is linked with only one strat, and a strat stores infomation:

    position max limit

    '''
    def __init__(self, store, tbname):
        self.store = store
        self.tbname = tbname
        self.strat = None
        self.stratposmax = None
        self.otypeconv = {
                fdef.KVOLUME:int,
                fdef.KPRICE:float,
                fdef.KISIOC:lambda x: x=='True',
                fdef.ISRESERVED:lambda x: x=='True'
                }

        self.ttypeconv = {
                fdef.KPOSITION:int,
                fdef.KRESERVED:int,
                fdef.KAVGPRICE:float,
                fdef.KMAXLIMIT:int
                }


        self.logger = logging.getLogger()
        self.name = self.__class__.__name__

    def setup(self):
        # read linked strat
        self.strat = self.store.hget(fdef.STRATTBMAP, self.tbname)
        # read strat's position limit
        pmaxkey = fdef.fullname(fdef.POSMAXNS, self.strat)
        self.stratposmax = self.store.hgetall(pmaxkey)
        self.stratposmax = [int(x) for x in self.stratposmax]
        return True

    def getalloid(self):
        rkey = fdef.fullname(fdef.ALLORDER, self.tbname)
        alloids = self.store.smembers(rkey)
        return alloids

    def getorder(self, oid):
        '''
        order and trade are stored separately in redis
        '''
        okey = fdef.fullname(fdef.ORDERNS, self.tbname, oid)
        tkey = fdef.fullname(fdef.TRADENS, self.tbname, oid)
        p = self.store.pipeline()
        p.hgetall(okey)
        p.lrange(tkey, 0, -1)
        order, traderaw = p.execute()

        try:
            trade = [Record.load(t) for t in traderaw]
        except:
            trade = []
            self.logger.exception('Load trade error.')
        for k in self.otypeconv:
            if k in order.keys():
                order[k] = self.otypeconv[k](order[k])
        order[fdef.KTRADE] = trade
        return order

    def updateorder(self, oid, toupdate):
        okey = fdef.fullname(fdef.ORDERNS, self.tbname, oid)
        self.store.hmset(okey, toupdate)

    def hasorder(self, oid):
        okey = fdef.fullname(fdef.ORDERNS, self.tbname, oid)
        aokey = fdef.fullname(fdef.ALLORDER, self.tbname)
        return self.store.sismember(aokey, okey)

    def neworder(self, oid, order):
        '''
        store order, trade is empty now, add oid in alloid
        '''
        o = deepcopy(order)
        if fdef.KTRADE in o:
            o.pop(fdef.KTRADE)

        okey = fdef.fullname(fdef.ORDERNS, self.tbname, oid)
        aokey = fdef.fullname(fdef.ALLORDER, self.tbname)
        p = self.store.pipeline()
        p.hmset(okey, o)
        p.sadd(aokey, okey)
        p.execute()

    def addtrade(self, oid, trade):
        # TODO: update position at the same time.
        pass

    def getallposkey(self):
        rkey = fdef.fullname(fdef.ALLTRADE, self.tbname)
        allposkey = self.store.smembers(rkey)
        return allposkey

    def getposition(self, poskey):
        pkey = fdef.fullname(fdef.POSITIONNS, self.tbname, poskey)
        pos = self.store.hgetall(pkey)
        for k in pos.keys():
            if k in self.ttypeconv:
                pos[k] = self.ttypeconv[k](pos[k])
        return pos

class TBookProxy(Thread):
    '''
    Receive queueed Tbook updates and
    1. store updates in redis using TBookLib,
    2. breadcasts update through pubsub.
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
            except Empty:
                pass

    def stop(self, dojoin=True):
        self.runflag = False
        if dojoin:
            self.queue.join()

    def process(self, br):
        try:
            self.tb.update(self.store, br)
            self.pubsub.publish(br)
        except:
            pass

    def getqueue(self):
        return self.queue

