# flare library in message passing style.
# flame = flare in message

import logging

import redis

from MdApi import MdApi, MdSpi
from TraderApi import TraderApi, TraderSpi  
import UserApiStruct as ustruct
import UserApiType as utype

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

class engine(Thread):
    '''
    engine works as a separate thread or process.
    It listens for order requests and provides handlers
    for CTP responses.
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

        self.oreflock = Lock()
        self.reqlock = Lock()

        # reverse map from exchangeID/OrderRef to oid
        self.exch2oid = {}
        self.oref2oid = {}
        self.maplock = Lock()

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
            t = self.pubsub.listen()
            self.reqorder(t)
        self.close()

    def setup(self):
        # start thread pool
        # start ctp api
        trader = TraderApi.CreateTraderApi(self.name)
        trader.RegisterSpi(self)
        trader.SubscribePublicTopic(THOST_TERT_QUICK)
        trader.SubscribePrivateTopic(THOST_TERT_QUICK)
        trader.RegisterFront(self.tradercfg.port)
        trader.Init()
        self.trader = trader
        self.loginevent.wait()

        if self.islogin:
            #self.orderman.addlogin(self.frontid,
            #        self.sessionid, self.api.GetTradingDay())
            #self.mysession = (self.frontid, self.sessionid)
            # TODO: check orderchannel
            self.pubsub.subscribe(orderchannel)

        return self.islogin

    def close(self):
        if self.trader:
            self.trader.Release()
            self.trader = None

    def stop(self):
        self.runflag = False

    def reqorder(self, t):
        # make ctp request
        # update reverse map
        # and submit
        pass

    # CTP handlers and helpers

    def isRspSuccess(self, RspInfo):
        return RspInfo is None or RspInfo.ErrorID == 0

    def ismysession(self, oref, order):
        # use oref or order?
        ret = False
        if self.islogin:
            # TODO: add other conditions
            ret = True
        return ret

    def getoid(refid, by='oref'):
        oid = None
        with self.maplock:
            try:
                if by == 'oref':
                    oid = self.oref2oid[refid]
                elif by == 'exch':
                    oid = self.exch2oid[refid]
            except KeyError:
                pass
        return oid

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

    # handlers for order response.
    # These handlers just publish responses in pubsub, while strats handlers,
    # orderman, tbook and monitors will do their jobs on receiving responses.

    # TODO: add settlement confirmation handlers?
    def OnRspOrderInsert(self, pInputOrder, pRspInfo, nRequestID, bIsLast):
        '''
            报单未通过参数校验,被CTP拒绝
            正常情况后不应该出现
        '''
        if pInputOrder is None or pRspInfo is None:
            return

        oreftp = self.makeoreftp(pInputOrder)
        if self.ismysession(oreftp):
            oid = self.getoid(oreftp)
            # TODO: make CTP neutral order: pInputOrder, pOrderAction and pTrade
            # NOTE: should include callback name such as OnRspOrderInsert

            self.pubsub.publish(order)

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
    def __init__(self, pubsub):
        Thread.__init__(self)
        self.runflag = True
        self.tbook = tbook
        self.pubsub = pubsub

    def run(self):
        while self.runflag:
            try:
                q = self.queue.get(True, 2)
                self.process(q)
            except Queue.Empty:
                pass

    def stop(self):
        self.runflag = False

    def process(self, q):
        # q is a quote, or any other inputs to generate trading signals.
        if q == 'open':
            self.pubsub.publish(Tbook, Reserve, oid)
            self.pubsub.publish(Engine, OpenOrder, oid)
        elif q == 'close':
            self.pubsub.publish(Engine, CloseOrder, oid)
        elif q == 'cancel':
            self.pubsub.publish(Tbook, Release, oid)
            self.pubsub.publish(Engine, Cancel, oid)


class TBook(Thread):
    '''
    TBook serves as trading book for one or more strategies.
    '''
    def __init__(self, pubsub):
        Thread.__init__(self)
        self.pubsub = pubsub
        self.runflag = True

    def run(self):
        while self.runflag:
            try:
                br = self.queue.get(True, 2)
                self.process(br)
            except Queue.Empty:
                pass

    def stop(self):
        self.runflag = False

    def process(self, br):
        pass