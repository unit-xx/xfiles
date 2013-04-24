#-*- coding:utf-8 -*-

# test ctp commands' req-resp flows

import time
import logging

import UserApiStruct as ustruct
import UserApiType as utype
from MdApi import MdApi, MdSpi
from TraderApi import TraderApi, TraderSpi  

THOST_TERT_RESTART  = 0
THOST_TERT_RESUME   = 1
THOST_TERT_QUICK    = 2

NFUNC = lambda data:None    #空函数桩

INSTS = [
         u'IF1305',u'IF1306',
         #u'zn1104',u'zn1105'
        ]
class BaseObject(object):
    def __init__(self,**kwargs):
        self.__dict__.update(kwargs)


    #has_attr/get_attr/set_attr没有必要, 系统函数hasattr/getattr/setattr已实现这些功能
    def has_attr(self,attr_name):
        return attr_name in self.__dict__

    def get_attr(self,attr_name):
        return self.__dict__[attr_name]

    def set_attr(self,attr_name,value):
        self.__dict__[attr_name] = value

    def __repr__(self):
        return 'BaseObject'

class TraderSpiDelegate(TraderSpi):
    '''
        将服务器回应转发到Agent
        并自行处理杂务
    '''
    logger = logging.getLogger('ctp.TraderSpiDelegate')    
    def __init__(self,
            instruments, #合约映射 name ==>c_instrument 
            broker_id,   #期货公司ID
            investor_id, #投资者ID
            passwd, #口令
            trader
        ):        
        self.instruments = set([name for name in instruments])
        self.broker_id =broker_id
        self.investor_id = investor_id
        self.passwd = passwd
        self.is_logged = False
        self.request_id = 1
        self.trader=trader

    def inc_order_ref(self):
        self.order_ref += 1
        return self.order_ref

    def isRspSuccess(self,RspInfo):
        return RspInfo == None or RspInfo.ErrorID == 0

    def login(self):
        self.logger.info(u'try login...')
        self.user_login(self.broker_id, self.investor_id, self.passwd)

    ##交易初始化
    def OnFrontConnected(self):
        '''
            当客户端与交易后台建立起通信连接时（还未登录前），该方法被调用。
        '''
        self.logger.info(u'TD:trader front connected')
        self.login()

    def OnFrontDisconnected(self, nReason):
        self.logger.info(u'TD:trader front disconnected,reason=%s' % (nReason,))

    def inc_request_id(self):
        self.request_id += 1
        return self.request_id

    def user_login(self, broker_id, investor_id, passwd):
        req = ustruct.ReqUserLogin(BrokerID=broker_id, UserID=investor_id, Password=passwd)
        r=self.api.ReqUserLogin(req,self.inc_request_id())

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        self.logger.info(u'TD:trader login, islast: %d' % bIsLast)
        self.logger.debug(u"TD:loggin %s" % str(pRspInfo))
        self.logger.debug(u"TD:loggin %s" % str(pRspUserLogin))
        if not self.isRspSuccess(pRspInfo):
            self.logger.warning(u'TD:trader login failed, errMsg=%s' %(pRspInfo.ErrorMsg,))
            print u'综合交易平台登陆失败，请检查网络或用户名/口令'
            self.is_logged = False
            return
        self.is_logged = True
        self.logger.info(u'TD:trader login success')
        self.login_success(pRspUserLogin.FrontID,pRspUserLogin.SessionID,pRspUserLogin.MaxOrderRef)
        #self.settlementInfoConfirm()
        #self.query_settlement_info()
        #self.query_settlement_confirm() 

    def login_success(self,frontID,sessionID,max_order_ref):
        self.front_id = frontID
        self.session_id = sessionID
        self.order_ref = int(max_order_ref)

    def OnRspUserLogout(self, pUserLogout, pRspInfo, nRequestID, bIsLast):
        '''登出请求响应'''
        self.logger.info(u'TD:trader logout')
        self.is_logged = False

    def resp_common(self,rsp_info,bIsLast,name='默认'):
        #self.logger.debug("resp: %s" % str(rsp_info))
        if not self.isRspSuccess(rsp_info):
            self.logger.info(u"TD:%s失败" % name)
            return -1
        elif bIsLast and self.isRspSuccess(rsp_info):
            self.logger.info(u"TD:%s成功" % name)
            return 1
        else:
            self.logger.info(u"TD:%s结果: 等待数据接收完全..." % name)
            return 0

    def query_settlement_confirm(self):
        '''
            这个基本没用，不如直接确认
            而且需要进一步明确：有史以来第一次确认前查询确认情况还是每天第一次确认查询情况时，返回的响应中
                pSettlementInfoConfirm为空指针. 如果是后者,则建议每日不查询确认情况,或者在generate_struct中对
                CThostFtdcSettlementInfoConfirmField的new_函数进行特殊处理
            CTP写代码的这帮家伙素质太差了，边界条件也不测试，后置断言也不整，空指针乱飞
            2011-3-1 确认每天未确认前查询确认情况时,返回的响应中pSettlementInfoConfirm为空指针
            并且妥善处理空指针之后,仍然有问题,在其中查询结算单无动静
        '''
        req = ustruct.QrySettlementInfoConfirm(BrokerID=self.broker_id,InvestorID=self.investor_id)
        self.api.ReqQrySettlementInfoConfirm(req,self.inc_request_id())

    def query_settlement_info(self):
        #不填日期表示取上一天结算单,并在响应函数中确认
        self.logger.info(u'TD:取上一日结算单信息并确认,BrokerID=%s,investorID=%s' % (self.broker_id,self.investor_id))
        req = ustruct.QrySettlementInfo(BrokerID=self.broker_id,InvestorID=self.investor_id,TradingDay=u'')
        #print req.BrokerID,req.InvestorID,req.TradingDay
        time.sleep(1)
        self.api.ReqQrySettlementInfo(req,self.inc_request_id())

    def confirm_settlement_info(self):
        self.logger.info(u'TD-CSI:准备确认结算单')
        req = ustruct.SettlementInfoConfirm(BrokerID=self.broker_id,InvestorID=self.investor_id)
        self.api.ReqSettlementInfoConfirm(req,self.inc_request_id())

    def OnRspQrySettlementInfo(self, pSettlementInfo, pRspInfo, nRequestID, bIsLast):
        '''请求查询投资者结算信息响应'''
        print u'Rsp 结算单查询'
        if(self.resp_common(pRspInfo,bIsLast,u'结算单查询')>0):
            self.logger.info(u'结算单查询完成,准备确认')
            try:
                self.logger.info(u'TD:结算单内容:%s' % pSettlementInfo.Content)
            except Exception,inst:
                self.logger.warning(u'TD-ORQSI-A 结算单内容错误:%s' % str(inst))
            self.confirm_settlement_info()
        else:  #这里是未完成分支,需要直接忽略
            try:
                self.logger.info(u'TD:结算单接收中...:%s' % pSettlementInfo.Content)
            except Exception,inst:
                self.logger.warning(u'TD-ORQSI-B 结算单内容错误:%s' % str(inst))
            #self.agent.initialize()
            pass
            

    def OnRspQrySettlementInfoConfirm(self, pSettlementInfoConfirm, pRspInfo, nRequestID, bIsLast):
        '''请求查询结算信息确认响应'''
        self.logger.debug(u"TD:结算单确认信息查询响应:rspInfo=%s,结算单确认=%s" % (pRspInfo,pSettlementInfoConfirm))
        #self.query_settlement_info()
        if(self.resp_common(pRspInfo,bIsLast,u'结算单确认情况查询')>0):
            if(pSettlementInfoConfirm == None or int(pSettlementInfoConfirm.ConfirmDate) < self.agent.scur_day):
                #其实这个判断是不对的，如果周日对周五的结果进行了确认，那么周一实际上已经不需要再次确认了
                if(pSettlementInfoConfirm != None):
                    self.logger.info(u'TD:最新结算单未确认，需查询后再确认,最后确认时间=%s,scur_day:%s' % (pSettlementInfoConfirm.ConfirmDate,self.agent.scur_day))
                else:
                    self.logger.info(u'TD:结算单确认结果为None')
                self.query_settlement_info()
            else:
                self.agent.isSettlementInfoConfirmed = True
                self.logger.info(u'TD:最新结算单已确认，不需再次确认,最后确认时间=%s,scur_day:%s' % (pSettlementInfoConfirm.ConfirmDate,self.agent.scur_day))
                self.agent.initialize()


    def OnRspSettlementInfoConfirm(self, pSettlementInfoConfirm, pRspInfo, nRequestID, bIsLast):
        '''投资者结算结果确认响应'''
        if(self.resp_common(pRspInfo,bIsLast,u'结算单确认')>0):
            self.agent.isSettlementInfoConfirmed = True
            self.logger.info(u'TD:结算单确认时间: %s-%s' %(pSettlementInfoConfirm.ConfirmDate,pSettlementInfoConfirm.ConfirmTime))
        self.agent.initialize()

    ###辅助   
    def rsp_qry_position(self,position):
        '''
            查询持仓回报, 每个合约最多得到4个持仓回报，历史多/空、今日多/空
        '''
        logging.info(u'持仓:%s' % str(position))

    def rsp_qry_instrument_marginrate(self,marginRate):
        '''
            查询保证金率回报. 
        '''
        logging.info(u'MarginLong:%.2f, MarginShort: %.2f'
                % (marginRate.LongMarginRatioByMoney,
                    marginRate.ShortMarginRatioByMoney))

    def rsp_qry_trading_account(self,account):
        '''
            查询资金帐户回报
        '''
        logging.info(u'account info: %s' % str(account))
    
    def rsp_qry_instrument(self,pinstrument):
        '''
            获得合约数量乘数. 
            这里的保证金率应该是和期货公司无关，所以不能使用
        '''
        logging.info(u'instruments info: %s' % str(pinstrument))

    def rsp_qry_position_detail(self,position_detail):
        '''
            查询持仓明细回报, 得到每一次成交的持仓,其中若已经平仓,则持量为0,平仓量>=1
            必须忽略
        '''
        logging.info(u'position info: %s', str(position_detail))

    ###交易准备
    def OnRspQryInstrumentMarginRate(self, pInstrumentMarginRate, pRspInfo, nRequestID, bIsLast):
        '''
            保证金率回报。返回的必然是绝对值
        '''
        if bIsLast and self.isRspSuccess(pRspInfo):
            self.rsp_qry_instrument_marginrate(pInstrumentMarginRate)
        else:
            #logging
            pass

    def OnRspQryInstrument(self, pInstrument, pRspInfo, nRequestID, bIsLast):
        '''
            合约回报。
        '''
        if bIsLast and self.isRspSuccess(pRspInfo):
            self.rsp_qry_instrument(pInstrument)
            #print pInstrument
        else:
            #logging
            #print pInstrument
            self.rsp_qry_instrument(pInstrument)  #模糊查询的结果,获得了多个合约的数据，只有最后一个的bLast是True


    def OnRspQryTradingAccount(self, pTradingAccount, pRspInfo, nRequestID, bIsLast):
        '''
            请求查询资金账户响应
        '''
        print u'查询资金账户响应'
        if self.isRspSuccess(pRspInfo):
            self.rsp_qry_trading_account(pTradingAccount)

    def OnRspQryInvestorPosition(self, pInvestorPosition, pRspInfo, nRequestID, bIsLast):
        '''请求查询投资者持仓响应'''
        #print u'查询持仓响应',str(pInvestorPosition),str(pRspInfo)
        if self.isRspSuccess(pRspInfo): #每次一个单独的数据报
            self.rsp_qry_position(pInvestorPosition)
        else:
            #logging
            pass

    def OnRspQryInvestorPositionDetail(self, pInvestorPositionDetail, pRspInfo, nRequestID, bIsLast):
        '''请求查询投资者持仓明细响应'''
        if self.isRspSuccess(pRspInfo): #每次一个单独的数据报
            self.rsp_qry_position_detail(pInvestorPositionDetail)
        else:
            #logging
            pass

    def OnRspError(self, info, RequestId, IsLast):
        ''' 错误应答
        '''
        self.logger.error(u'TD:requestID:%s,IsLast:%s,info:%s' % (RequestId,IsLast,str(info)))

    def OnRspQryOrder(self, pOrder, pRspInfo, nRequestID, bIsLast):
        '''请求查询报单响应'''
        if self.isRspSuccess(pRspInfo):
            self.logger.info('QryOrder: %s' % repr(pOrder))
        else:
            self.logger.error(u'TD:requestID:%s,IsLast:%s,info:%s' % (nRequestID,bIsLast,repr(pRspInfo)))
            pass

    def OnRspQryTrade(self, pTrade, pRspInfo, nRequestID, bIsLast):
        '''请求查询成交响应'''
        if self.isRspSuccess(pRspInfo):
            self.logger.info('QryTrade: %s' % str(Trade))
        else:
            #logging
            pass


    ###交易操作
    def OnRspOrderInsert(self, pInputOrder, pRspInfo, nRequestID, bIsLast):
        '''
            报单未通过参数校验,被CTP拒绝
            正常情况后不应该出现
        '''
        print pRspInfo,nRequestID
        self.logger.warning(u'TD:CTP报单录入错误回报, 正常后不应该出现,rspInfo=%s'%(str(pRspInfo),))
        #self.logger.warning(u'报单校验错误,ErrorID=%s,ErrorMsg=%s,pRspInfo=%s,bIsLast=%s' % (pRspInfo.ErrorID,pRspInfo.ErrorMsg,str(pRspInfo),bIsLast))
        #self.agent.rsp_order_insert(pInputOrder.OrderRef,pInputOrder.InstrumentID,pRspInfo.ErrorID,pRspInfo.ErrorMsg)
    
    def OnErrRtnOrderInsert(self, pInputOrder, pRspInfo):
        '''
            交易所报单录入错误回报
            正常情况后不应该出现
            这个回报因为没有request_id,所以没办法对应
        '''
        print u'ERROR Order Insert'
        self.logger.warning(u'TD:交易所报单录入错误回报, 正常后不应该出现,rspInfo=%s'%(str(pRspInfo),))
   
    def OnRtnOrder(self, pOrder):
        ''' 报单通知
            CTP、交易所接受报单
            Agent中不区分，所得信息只用于撤单
        '''
        #print repr(pOrder)
        self.logger.info(u'报单响应,Order=%s' % str(pOrder))
        if pOrder.OrderStatus == 'a':
            #CTP接受，但未发到交易所
            #print u'CTP接受Order，但未发到交易所, BrokerID=%s,BrokerOrderSeq = %s,TraderID=%s, OrderLocalID=%s' % (pOrder.BrokerID,pOrder.BrokerOrderSeq,pOrder.TraderID,pOrder.OrderLocalID)
            self.logger.info(u'TD:CTP接受Order，但未发到交易所, BrokerID=%s,BrokerOrderSeq = %s,TraderID=%s, OrderLocalID=%s' % (pOrder.BrokerID,pOrder.BrokerOrderSeq,pOrder.TraderID,pOrder.OrderLocalID))
        else:
            #print u'交易所接受Order,exchangeID=%s,OrderSysID=%s,TraderID=%s, OrderLocalID=%s' % (pOrder.ExchangeID,pOrder.OrderSysID,pOrder.TraderID,pOrder.OrderLocalID)
            self.logger.info(u'TD:交易所接受Order,exchangeID=%s,OrderSysID=%s,TraderID=%s, OrderLocalID=%s' % (pOrder.ExchangeID,pOrder.OrderSysID,pOrder.TraderID,pOrder.OrderLocalID))
            #self.agent.rtn_order_exchange(pOrder)

    def OnRtnTrade(self, pTrade):
        '''成交通知'''
        self.logger.info(u'TD:成交通知,BrokerID=%s,BrokerOrderSeq = %s,exchangeID=%s,OrderSysID=%s,TraderID=%s, OrderLocalID=%s' %(pTrade.BrokerID,pTrade.BrokerOrderSeq,pTrade.ExchangeID,pTrade.OrderSysID,pTrade.TraderID,pTrade.OrderLocalID))
        self.rtn_trade(pTrade)

    def rtn_trade(self,strade):
        '''
            成交回报
            #TODO: 必须考虑出现平仓信号时，position还没完全成交的情况
                   在OnTrade中进行position的细致处理 
            #TODO: 必须处理策略分类持仓汇总和持仓总数不匹配时的问题
        '''
        logging.info(u'A_RT1:成交回报,%s:orderref=%s,price=%s' % (strade.InstrumentID,strade.OrderRef,strade.Price))

    def err_order_action(self,order_ref,instrument_id,error_id,error_msg):
        '''
            ctp/交易所撤单错误回报，不区分ctp和交易所
            必须处理，如果已成交，撤单后必然到达这个位置
        '''
        logging.info(u'撤单时已成交，error_id=%s,error_msg=%s' %(error_id,error_msg))
        
    def OnRspOrderAction(self, pInputOrderAction, pRspInfo, nRequestID, bIsLast):
        '''
            ctp撤单校验错误
        '''
        self.logger.warning(u'TD:CTP撤单录入错误回报, 正常后不应该出现,rspInfo=%s'%(str(pRspInfo),))
        #self.agent.rsp_order_action(pInputOrderAction.OrderRef,pInputOrderAction.InstrumentID,pRspInfo.ErrorID,pRspInfo.ErrorMsg)
        self.err_order_action(pInputOrderAction.OrderRef,pInputOrderAction.InstrumentID,pRspInfo.ErrorID,pRspInfo.ErrorMsg)

    def OnErrRtnOrderAction(self, pOrderAction, pRspInfo):
        ''' 
            交易所撤单操作错误回报
            正常情况后不应该出现
        '''
        self.logger.warning(u'TD:交易所撤单录入错误回报, 可能已经成交,rspInfo=%s'%(str(pRspInfo),))
        self.err_order_action(pOrderAction.OrderRef,pOrderAction.InstrumentID,pRspInfo.ErrorID,pRspInfo.ErrorMsg)

    def open_position(self,order):
        ''' 
            发出下单指令
        '''
        req = ustruct.InputOrder(
                InstrumentID = order.instrument,
                Direction = order.direction,
                OrderRef = str(order.order_ref),
                LimitPrice = order.price,   #有个疑问，double类型如何保证舍入舍出，在服务器端取整?
                VolumeTotalOriginal = order.volume,
                OrderPriceType = utype.THOST_FTDC_OPT_LimitPrice,
                
                BrokerID = self.broker_id,
                InvestorID = self.investor_id,
                CombOffsetFlag = utype.THOST_FTDC_OF_Open,         #开仓 5位字符,但是只用到第0位
                CombHedgeFlag = utype.THOST_FTDC_HF_Speculation,   #投机 5位字符,但是只用到第0位

                VolumeCondition = utype.THOST_FTDC_VC_AV,
                MinVolume = 1,  #这个作用有点不确定,有的文档设成0了
                ForceCloseReason = utype.THOST_FTDC_FCC_NotForceClose,
                IsAutoSuspend = 1,
                UserForceClose = 0,
                TimeCondition = utype.THOST_FTDC_TC_GFD,
            )
        logging.info(u'下单: instrument=%s,方向=%s,数量=%s,价格=%s,OrderRef=%d' % (order.instrument,u'多' if order.direction==utype.THOST_FTDC_D_Buy else u'空',order.volume,order.price,order.order_ref))
        r = self.api.ReqOrderInsert(req,self.inc_request_id())

    def fetch_trading_account(self):
        #获取资金帐户
        logging.info(u'A:获取资金帐户..')
        req = ustruct.QryTradingAccount(BrokerID=self.broker_id, InvestorID=self.investor_id)
        r=self.api.ReqQryTradingAccount(req,self.inc_request_id())

    def fetch_investor_position(self,instrument_id):
        #获取合约的当前持仓
        logging.info(u'A:获取合约%s的当前持仓..' % (instrument_id,))
        req = ustruct.QryInvestorPosition(BrokerID=self.broker_id, InvestorID=self.investor_id,InstrumentID=instrument_id)
        r=self.api.ReqQryInvestorPosition(req,self.inc_request_id())
        logging.info(u'A:查询持仓, 函数发出返回值:%s' % r)
    
    def fetch_investor_position_detail(self,instrument_id):
        '''
            获取合约的当前持仓明细，目前没用
        '''
        logging.info(u'A:获取合约%s的当前持仓..' % (instrument_id,))
        req = ustruct.QryInvestorPositionDetail(BrokerID=self.broker_id, InvestorID=self.investor_id,InstrumentID=instrument_id)
        r=self.api.ReqQryInvestorPositionDetail(req,self.inc_request_id())
        logging.info(u'A:查询持仓明细, 函数发出返回值:%s' % r)

    def fetch_instrument_marginrate(self,instrument_id):
        req = ustruct.QryInstrumentMarginRate(BrokerID=self.broker_id,
                        InvestorID=self.investor_id,
                        InstrumentID=instrument_id,
                        HedgeFlag = utype.THOST_FTDC_HF_Speculation
                )
        r = self.api.ReqQryInstrumentMarginRate(req,self.inc_request_id())
        logging.info(u'A:查询保证金率, 函数发出返回值:%s' % r)

    def fetch_instrument(self,instrument_id):
        req = ustruct.QryInstrument(
                        InstrumentID=instrument_id,
                )
        r = self.api.ReqQryInstrument(req,self.inc_request_id())
        logging.info(u'A:查询合约, 函数发出返回值:%s' % r)

    def fetch_orders(self, instrument_id):
        req = ustruct.QryOrder(
                        InstrumentID=instrument_id,
                )
        r = self.api.ReqQryOrder(req,self.inc_request_id())
        logging.info(u'A:查询报单, 函数发出返回值:%s' % r)


def main():
    logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s | %(levelname)s | %(pathname)s | %(funcName)s | L:%(lineno)d | P:%(process)d | T:%(threadName)s | TID:%(thread)d | %(message)s'
            #format='%(name)s:%(funcName)s:%(lineno)d:%(asctime)s %(levelname)s %(message)s'
            )

    logging.info('')
    logging.info('======================')
    trader = TraderApi.CreateTraderApi("trader")

    myspi = TraderSpiDelegate(instruments=INSTS, 
                             broker_id='1021',
                             investor_id= "00000062",
                             passwd= "4617011",
                             trader=trader
                       )
    trader.RegisterSpi(myspi)
    trader.myspi = myspi
    trader.SubscribePublicTopic(THOST_TERT_QUICK)
    trader.SubscribePrivateTopic(THOST_TERT_QUICK)
    trader.RegisterFront("tcp://180.169.124.2:21205")
    #trader.RegisterFront("tcp://180.169.124.2:21213") this is for MD
    trader.Init()

    time.sleep(1)

    #morder = BaseObject(instrument='IF1305',direction='0',order_ref=myspi.inc_order_ref(),price=2446,volume=1)
    #myspi.open_position(morder)

    #myspi.fetch_trading_account()
    #time.sleep(1)

    #myspi.fetch_investor_position(u'IF1305')
    #time.sleep(1)

    #myspi.fetch_instrument_marginrate(u'IF1305')
    #time.sleep(1)

    #myspi.fetch_instrument(u'IF1305')
    #time.sleep(1)

    #myspi.fetch_investor_position_detail(u'IF1305')
    #time.sleep(1)

    myspi.fetch_orders(u'IF1305')
    time.sleep(1)

    while 1:
        time.sleep(1)

if __name__=='__main__':
    main()
