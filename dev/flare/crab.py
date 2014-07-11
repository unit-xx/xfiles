# CalendaR ARbitrage.

import sys
import cPickle as pickle
from threading import Thread, Lock
from math import floor, ceil
from collections import defaultdict
from datetime import datetime

from flamelib import stratconsole, runstrat, strattop
import flaredef as fdef
import config

class crabstrat(strattop):
    def setup(self):
        self.chma = self.mycfg['machannel']
        self.maxvolperorder = int(self.mycfg['maxvolperorder'])

        self.quickleg = self.mycfg['quickleg']
        self.lazyleg = self.mycfg['lazyleg']
        self.sigma = float(self.mycfg['sigma'])
        self.intensity = float(self.mycfg['intensity'])
        self.delta = self.intensity + self.sigma/2
        self.qmax = int(self.mycfg['qmax'])

        # using MA value to calc midprice of spread
        # store ticku and value for each leg.
        self.midprice = defaultdict(dict)
        self.qhold = 0
        self.sprdmid = None
        self.sprdmidfix = None

        self.lazylegoid = {
                'ask':None,
                'bid':None
                }
        self.lazyordersetok = {
                'ask':False,
                'bid':False
                }
        self.quicklegoid = None

        self.quickquote = None
        self.lazyquote = None

        self.lazyerroid = None

        self.quickmidprice = None

        self.lastlazyask = 0.0
        self.lastlazybid = 0.0

        self.quickstate = 'ready'
        self.lazystate = 'ready'
        self.sprdaskmode = 'empty'
        self.sprdbidmode = 'empty'

        self.delaytask = None

        self.lock = Lock()

        # intentially set to suspended at startup
        self.suspendflag = True

        self.pubsub.subscribe((fdef.CHQUOTE, self.chma, fdef.CHHEARTBEAT))

        return True

    def riskcheck(self, oid):
        o, olk = self.tbook.getorder(oid)
        ret = False
        if o is not None:
            with olk:
                vol = o[fdef.KVOLUME]
                if vol <= self.maxvolperorder:
                    ret = True
                else:
                    ret = False
        #self.logger.debug('order %s rc result: %s', oid, ret)
        return ret

    def floor02(self, x):
        return 0.2*floor(x/0.2)

    def ceil02(self, x):
        return 0.2*ceil(x/0.2)

    def round02(self, x):
        return 0.2*round(x/0.2)

    def quote2str(self, q):
        keys = ('code', 'ask1', 'askvol1', 'bid1', 'bidvol1', 'time', 'msec', 'tic')
        fmt = ('s', '.2f', 'd', '.2f', 'd', 's', 'd', '.2f')
        
        fmt = ['%%(%s)%s'%(x[0],x[1]) for x in zip(keys, fmt)]

        s = ' '.join([' '.join(x) for x in zip(keys, fmt)])
        return s % q

    def issuspend(self):
        return (self.suspendflag==True and self.qhold==0 and self.lazystate=='ready' and self.quickstate=='ready')

    def dosuspend(self):
        self.suspendflag = True

    def dounsuspend(self):
        self.suspendflag = False

    def signal(self, m):
        '''
        set limit orders of lazyleg on both ask and bid, when one 
        of the orders are traded, immediately trade the quickleg.

        prerequirement:
        latest MA for both legs
        latest quote for both legs

        set limit order of lazyleg, with price calc from sprd MA,
        sigma, intensity and quickleg's quote.

        On lazyleg traded:
            trade quickleg ASAP and cancel untraded lazyleg

        On MA or quickleg's quote changed (lazyleg not traded):
            cancel and reset lazyleg's limit order
        '''

        self.lock.acquire()
        #self.logger.debug('enter signal')

        isresetlazy = False

        if m['channel'] == fdef.CHQUOTE:
            try:
                q = pickle.loads(m['data'])
            except:
                print 'quote unpickling failed.'
                self.lock.release()
                #self.logger.debug('exit signal')
                return

            # if midprice of quickleg is changed, reset lazyleg order
            if q['code'] == self.quickleg:
                if q['bid1']>q['upperlimit'] or q['bid1']<q['lowerlimit'] or q['ask1']>q['upperlimit'] or q['ask1']<q['lowerlimit']:
                    pass
                else:
                    self.quickquote = q
                    newquickmid = (q['bid1'] + q['ask1'])/2

                    self.logger.info('new quick quote %s', self.quote2str(q))

                    if self.quickmidprice is None or abs(newquickmid-self.quickmidprice)>0.05:
                        #print 'new mid: %.3f' % newquickmid
                        if newquickmid is not None and self.quickmidprice is not None:
                            self.logger.info('new quickmid %.3f <- %.3f', newquickmid, self.quickmidprice)
                        self.quickmidprice = newquickmid
                        isresetlazy = True

            elif q['code']==self.lazyleg:
                if q['bid1']>q['upperlimit'] or q['bid1']<q['lowerlimit'] or q['ask1']>q['upperlimit'] or q['ask1']<q['lowerlimit']:
                    pass
                else:
                    self.lazyquote = q
                    self.logger.info('new lazy quote %s', self.quote2str(q))

        elif m['channel'] == self.chma:
            try:
                inst, tickunit, maval = pickle.loads(m['data'])
            except:
                self.lock.release()
                #self.logger.debug('exit signal')
                return

            if inst==self.quickleg or inst==self.lazyleg:
                self.midprice[inst]['ticku'] = tickunit
                self.midprice[inst]['value'] = maval
                try:
                    # if midprice of sprd is changed, reset lazyleg order
                    if self.midprice[self.quickleg]['ticku']==self.midprice[self.lazyleg]['ticku']:
                        newsprdmid = self.midprice[self.lazyleg]['value'] - self.midprice[self.quickleg]['value']
                        if self.sprdmid is None or abs(newsprdmid-self.sprdmid)>0.05:
                            if newsprdmid is not None and self.sprdmid is not None:
                                self.logger.info('new sprdmid %.3f <- %.3f', newsprdmid, self.sprdmid)
                            self.sprdmid = newsprdmid
                            self.sprdmidfix = self.sprdmid - self.qhold * self.sigma
                            #print 'new sprdmid: %.3f' % newsprdmid
                            isresetlazy = True

                except KeyError:
                    # ma hasn't been received for some legs.
                    pass
                except TypeError:
                    # ma is none since not enough quotes is accumulated to calc ma
                    pass

        if self.sprdmid is None or self.sprdmidfix is None or self.quickmidprice is None or self.quickquote is None or self.lazyquote is None:
            self.lock.release()
            #self.logger.debug('exit signal')
            return

        if self.issuspend():
            self.lock.release()
            return

        if self.lazystate=='ready' and self.quickstate=='ready':
            # set limit order of lazyleg
            lazyask = self.sprdmidfix + self.quickmidprice + self.delta
            lazybid = self.sprdmidfix + self.quickmidprice - self.delta
            lazyask = self.round02(lazyask)
            lazybid = self.round02(lazybid)

            if self.qhold==0:
                self.sprdaskmode = 'openshort'
                self.sprdbidmode = 'openlong'
                print 'qhold=0'
            elif self.qhold > 0:
                self.sprdaskmode = 'closelong'
                self.sprdbidmode = 'openlong'
                print 'qhold>0'
            elif self.qhold < 0:
                self.sprdaskmode = 'openshort'
                self.sprdbidmode = 'closeshort'
                print 'qhold<0'

            if self.qhold==self.qmax:
                self.sprdbidmode = 'empty'
            elif self.qhold==-self.qmax:
                self.sprdaskmode = 'empty'

            print self.sprdaskmode, self.sprdbidmode

            # set ask side
            askoid = None
            if self.sprdaskmode=='openshort':
                # open short lazy leg
                otype = fdef.VOPEN
                direct = fdef.VSHORT
                code = self.lazyleg
                price = lazyask
                volume = 1
                askoid, doreq, rcok = self.reqorder(otype, direct, code, price, volume)
                print 'set ask as open short'
                self.lazyordersetok['ask'] = False
                # urgent case if doreq is False
            elif self.sprdaskmode=='closelong':
                otype = fdef.VCLOSE
                direct = fdef.VLONG
                code = self.lazyleg
                price = lazyask
                volume = 1
                askoid, doreq, rcok = self.reqorder(otype, direct, code, price, volume)
                print 'set ask as close long'
                self.lazyordersetok['ask'] = False
                # urgent case if doreq is False
            else:
                # empty
                self.lazyordersetok['ask'] = True
                print 'set ask as empty'
                pass
            self.lazylegoid['ask'] = askoid

            # set bid side
            bidoid = None
            if self.sprdbidmode=='openlong':
                otype = fdef.VOPEN
                direct = fdef.VLONG
                code = self.lazyleg
                price = lazybid
                volume = 1
                bidoid, doreq, rcok = self.reqorder(otype, direct, code, price, volume)
                print 'set bid as open long'
                self.lazyordersetok['bid'] = False
                # urgent case if doreq is False
            elif self.sprdbidmode=='closeshort':
                otype = fdef.VCLOSE
                direct = fdef.VSHORT
                code = self.lazyleg
                price = lazybid
                volume = 1
                bidoid, doreq, rcok = self.reqorder(otype, direct, code, price, volume)
                print 'set bid as close short'
                self.lazyordersetok['bid'] = False
                # urgent case if doreq is False
            else:
                # empty
                self.lazyordersetok['bid'] = True
                print 'set bid as empty'
                pass
            self.lazylegoid['bid'] = bidoid

            oldlazystate = self.lazystate
            oldquickstate = self.quickstate
            oldqhold = self.qhold
            self.lazystate = 'setting'

            print('set lazy limit: lazystate=%s(<-%s) quickstate=%s(<-%s) q=%d(<-%d) sprdmid=%.3f sprdfix=%.3f quickmid=%.2f delta=%.3f lazyask=%.2f lazybid=%.2f ' % (self.lazystate, oldlazystate, self.quickstate, oldquickstate, self.qhold, oldqhold, self.sprdmid, self.sprdmidfix, self.quickmidprice, self.delta, lazyask, lazybid))

            self.logger.info('set lazy limit: lazystate=%s(<-%s) quickstate=%s(<-%s) q=%d(<-%d) sprdmid=%.3f sprdfix=%.3f quickmid=%.2f delta=%.3f setlazybid=%.2f setlazyask=%.2f lastsetlazybid=%.2f lastsetlazyask=%.2f quickbid=%.2f quickask=%.2f quicktick=%.2f lazybid=%.2f lazyask=%.2f lazytick=%.2f' % (self.lazystate, oldlazystate, self.quickstate, oldquickstate, self.qhold, oldqhold, self.sprdmid, self.sprdmidfix, self.quickmidprice, self.delta, lazybid, lazyask, self.lastlazybid, self.lastlazyask, self.quickquote['bid1'], self.quickquote['ask1'], self.quickquote['tic'], self.lazyquote['bid1'], self.lazyquote['ask1'], self.lazyquote['tic']))

            self.lastlazybid = lazybid
            self.lastlazyask = lazyask

        elif self.lazystate=='set' and isresetlazy:
            lazyask = self.sprdmidfix + self.quickmidprice + self.delta
            lazybid = self.sprdmidfix + self.quickmidprice - self.delta
            lazyask = self.round02(lazyask)
            lazybid = self.round02(lazybid)

            if (abs(lazyask-self.lastlazyask)>1e-6) and (abs(lazybid-self.lastlazybid)>1e-6):
                # cancel first
                if self.lazylegoid['ask'] is not None:
                    self.cancelorder(self.lazylegoid['ask'])

                if self.lazylegoid['bid'] is not None:
                    self.cancelorder(self.lazylegoid['bid'])

                oldlazystate = self.lazystate
                oldquickstate = self.quickstate
                oldqhold = self.qhold
                self.lazystate = 'cancelling'

                print('cancel both lazy limit: lazystate=%s(<-%s) quickstate=%s(<-%s) q=%d(<-%d) sprdmid=%.3f sprdfix=%.3f quickmid=%.2f, delta=%.3f' % (self.lazystate, oldlazystate, self.quickstate, oldquickstate, self.qhold, oldqhold, self.sprdmid, self.sprdmidfix, self.quickmidprice, self.delta))
                #self.logger.info('cancel both lazy limit: lazystate=%s(<-%s) quickstate=%s(<-%s) q=%d(<-%d) sprdmid=%.3f sprdfix=%.3f quickmid=%.2f, delta=%.3f newlazybid=%.3f newlazyask=%.3f lastlazybid=%.3f lastlazyask=%.3f' % (self.lazystate, oldlazystate, self.quickstate, oldquickstate, self.qhold, oldqhold, self.sprdmid, self.sprdmidfix, self.quickmidprice, self.delta, lazybid, lazyask, self.lastlazybid, self.lastlazyask))
            else:
                print 'no need to cancel lazy'
        else:
            oldlazystate = self.lazystate
            oldquickstate = self.quickstate
            oldqhold = self.qhold

            #print('info: lazystate=%s(<-%s) quickstate=%s(<-%s) q=%d(<-%d) sprdmid=%.3f sprdfix=%.3f quickmid=%.2f, delta=%.3f' % (self.lazystate, oldlazystate, self.quickstate, oldquickstate, self.qhold, oldqhold, self.sprdmid, self.sprdmidfix, self.quickmidprice, self.delta,))

        self.lock.release()
        #self.logger.debug('exit signal')

    def OnOrderFullyTrade(self, oid, resp):

        self.lock.acquire()
        #self.logger.debug('enter OnOrderFullyTrade')
        print 'fully trade'

        # whose order? lazyleg or quickleg?
        o, olk = self.tbook.getorder(oid)
        if o[fdef.KCODE]==self.quickleg:
            print 'quick fully trade'
            # quickleg should be in 'ordered' state
            # set quickleg state to ready
            lazyotype = o[fdef.KOTYPE]
            lazydirect = fdef.VSHORT if o[fdef.KDIR]==fdef.VLONG else fdef.VLONG

            oldqhold = self.qhold
            if (lazyotype==fdef.VOPEN and lazydirect==fdef.VSHORT) or (lazyotype==fdef.VCLOSE and lazydirect==fdef.VLONG):
                # sprd ask side is traded
                self.qhold = self.qhold - 1
            else:
                # sprd bid side is traded
                self.qhold = self.qhold + 1
            if self.qhold==0:
                self.tbook.printpnl()

            oldlazystate = self.lazystate
            oldquickstate = self.quickstate
            self.quickstate = 'ready'
            self.sprdmidfix = self.sprdmid - self.qhold * self.sigma

            print('quick traded: lazystate=%s(<-%s) quickstate=%s(<-%s) q=%d(<-%d) sprdmid=%.3f sprdfix=%.3f quickmid=%.2f, delta=%.3f' % (self.lazystate, oldlazystate, self.quickstate, oldquickstate, self.qhold, oldqhold, self.sprdmid, self.sprdmidfix, self.quickmidprice, self.delta))

        elif o[fdef.KCODE]==self.lazyleg:
            # lazyleg should be in 'set' state
            # lazyleg to cancelother state
            # cancel other lazyleg
            print 'lazy fully trade'
            if self.lazystate=='set' or self.lazystate=='setting':
                # setting when: a lazy leg is traded even before the other lazy is accepeted
                if oid==self.lazylegoid['ask']:
                    # ask side traded, cancel bid side
                    self.lazylegoid['ask'] = None
                    print 'ask traded'
                    self.logger.info('ask traded, quickbid=%.2f quickask=%.2f quicktick=%.2f lazybid=%.2f lazyask=%.2f lazytick=%.2f' % (self.quickquote['bid1'], self.quickquote['ask1'], self.quickquote['tic'], self.lazyquote['bid1'], self.lazyquote['ask1'], self.lazyquote['tic']))
                    if self.lazylegoid['bid'] is not None:
                        self.cancelorder(self.lazylegoid['bid'])
                        print 'cancel bid as other'
                elif oid==self.lazylegoid['bid']:
                    self.lazylegoid['bid'] = None
                    print 'bid traded'
                    self.logger.info('bid traded, quickbid=%.2f quickask=%.2f quicktick=%.2f lazybid=%.2f lazyask=%.2f lazytick=%.2f' % (self.quickquote['bid1'], self.quickquote['ask1'], self.quickquote['tic'], self.lazyquote['bid1'], self.lazyquote['ask1'], self.lazyquote['tic']))
                    if self.lazylegoid['ask'] is not None:
                        self.cancelorder(self.lazylegoid['ask'])
                        print 'cancel ask as other'

                if self.lazylegoid['ask'] is None and self.lazylegoid['bid'] is None:
                    # when +/-qmax is reached only either bid or ask is set
                    oldlazystate = self.lazystate
                    self.lazystate = 'ready'
                else:
                    oldlazystate = self.lazystate
                    self.lazystate = 'cancelother'

                # quick leg should in ready state, otherwise it is urgent
                # order quick leg
                otype = o[fdef.KOTYPE]
                direct = fdef.VSHORT if o[fdef.KDIR]==fdef.VLONG else fdef.VLONG
                code = self.quickleg
                if (otype==fdef.VOPEN and direct==fdef.VSHORT) or (otype==fdef.VCLOSE and direct==fdef.VLONG):
                    price = self.quickquote['bid1'] - 5.0 
                else:
                    price = self.quickquote['ask1'] + 5.0
                volume = 1
                quickoid, doreq, rcok = self.reqorder(otype, direct, code, price, volume)
                self.quicklegoid = quickoid
                oldquickstate = self.quickstate
                self.quickstate = 'orderring'

                oldqhold = self.qhold
                print('order quick at fully trade: lazystate=%s(<-%s) quickstate=%s(<-%s) q=%d(<-%d) sprdmid=%.3f sprdfix=%.3f quickmid=%.2f, delta=%.3f' % (self.lazystate, oldlazystate, self.quickstate, oldquickstate, self.qhold, oldqhold, self.sprdmid, self.sprdmidfix, self.quickmidprice, self.delta))
                self.logger.info('order quick at fully trade: lazystate=%s(<-%s) quickstate=%s(<-%s) q=%d(<-%d) sprdmid=%.3f sprdfix=%.3f quickmid=%.2f, delta=%.3f quickbid=%.2f quickask=%.2f quicktick=%.2f lazybid=%.2f lazyask=%.2f lazytick=%.2f' % (self.lazystate, oldlazystate, self.quickstate, oldquickstate, self.qhold, oldqhold, self.sprdmid, self.sprdmidfix, self.quickmidprice, self.delta, self.quickquote['bid1'], self.quickquote['ask1'], self.quickquote['tic'], self.lazyquote['bid1'], self.lazyquote['ask1'], self.lazyquote['tic']))
            elif self.lazystate=='cancelling':
                # cancel-while-traded race condition.
                if oid==self.lazylegoid['ask']:
                    self.lazylegoid['ask'] = None
                    print 'ask traded'
                    self.logger.info('ask traded, quickbid=%.2f quickask=%.2f quicktick=%.2f lazybid=%.2f lazyask=%.2f lazytick=%.2f' % (self.quickquote['bid1'], self.quickquote['ask1'], self.quickquote['tic'], self.lazyquote['bid1'], self.lazyquote['ask1'], self.lazyquote['tic']))
                elif oid==self.lazylegoid['bid']:
                    self.lazylegoid['bid'] = None
                    print 'bid traded'
                    self.logger.info('bid traded, quickbid=%.2f quickask=%.2f quicktick=%.2f lazybid=%.2f lazyask=%.2f lazytick=%.2f' % (self.quickquote['bid1'], self.quickquote['ask1'], self.quickquote['tic'], self.lazyquote['bid1'], self.lazyquote['ask1'], self.lazyquote['tic']))

                if self.lazylegoid['ask'] is None and self.lazylegoid['bid'] is None:
                    # both lazy leg is None because 1. one of them is not set 2. one of them is cancelled first normally
                    oldlazystate = self.lazystate
                    self.lazystate = 'ready'
                else:
                    oldlazystate = self.lazystate
                    self.lazystate = 'cancelother'

                # order quick leg
                otype = o[fdef.KOTYPE]
                direct = fdef.VSHORT if o[fdef.KDIR]==fdef.VLONG else fdef.VLONG
                code = self.quickleg
                if (otype==fdef.VOPEN and direct==fdef.VSHORT) or (otype==fdef.VCLOSE and direct==fdef.VLONG):
                    price = self.quickquote['bid1'] - 5.0 
                else:
                    price = self.quickquote['ask1'] + 5.0
                volume = 1
                quickoid, doreq, rcok = self.reqorder(otype, direct, code, price, volume)
                self.quicklegoid = quickoid
                oldquickstate = self.quickstate
                self.quickstate = 'orderring'

                oldqhold = self.qhold
                print('order quick at cancelling: lazystate=%s(<-%s) quickstate=%s(<-%s) q=%d(<-%d) sprdmid=%.3f sprdfix=%.3f quickmid=%.2f, delta=%.3f' % (self.lazystate, oldlazystate, self.quickstate, oldquickstate, self.qhold, oldqhold, self.sprdmid, self.sprdmidfix, self.quickmidprice, self.delta))
                self.logger.info('order quick at cancelling: lazystate=%s(<-%s) quickstate=%s(<-%s) q=%d(<-%d) sprdmid=%.3f sprdfix=%.3f quickmid=%.2f, delta=%.3f quickbid=%.2f quickask=%.2f quicktick=%.2f lazybid=%.2f lazyask=%.2f lazytick=%.2f' % (self.lazystate, oldlazystate, self.quickstate, oldquickstate, self.qhold, oldqhold, self.sprdmid, self.sprdmidfix, self.quickmidprice, self.delta, self.quickquote['bid1'], self.quickquote['ask1'], self.quickquote['tic'], self.lazyquote['bid1'], self.lazyquote['ask1'], self.lazyquote['tic']))
            elif self.lazystate=='cancelother':
                # very special case that both lazy leg is traded.
                # it is closed as soon as possible.
                errorleg = 'empty'
                if oid==self.lazylegoid['ask']:
                    self.lazylegoid['ask'] = None
                    errorleg = 'ask'
                    print 'corner case: ask traded'
                elif oid==self.lazylegoid['bid']:
                    self.lazylegoid['bid'] = None
                    errorleg = 'bid'
                    print 'corner case: bid traded'

                # both lazy leg oid should be None now
                if self.lazylegoid['ask'] is None and self.lazylegoid['bid'] is None:
                    if errorleg=='ask':
                        if self.sprdaskmode=='openshort':
                            # close short the error leg
                            otype = fdef.VCLOSE
                            direct = fdef.VSHORT
                            code = self.lazyleg
                            price = self.lazyquote['ask1'] + 5.0
                            volume = 1
                            tag = 'errlazy.openshort'
                            self.lazyerroid, doreq, rcok = self.reqorder(otype, direct, code, price, volume, tag=tag)
                        elif self.sprdaskmode=='closelong':
                            # re-open long
                            otype = fdef.VOPEN
                            direct = fdef.VLONG
                            code = self.lazyleg
                            price = self.lazyquote['ask1'] + 5.0
                            volume = 1
                            tag = 'errlazy.closelong'
                            self.lazyerroid, doreq, rcok = self.reqorder(otype, direct, code, price, volume, tag=tag)
                    elif errorleg=='bid':
                        if self.sprdbidmode=='openlong':
                            # close long the error leg
                            otype = fdef.VCLOSE
                            direct = fdef.VLONG
                            code = self.lazyleg
                            price = self.lazyquote['bid1'] - 5.0
                            volume = 1
                            tag = 'errlazy.openlong'
                            self.lazyerroid, doreq, rcok = self.reqorder(otype, direct, code, price, volume, tag=tag)
                        elif self.sprdbidmode=='closeshort':
                            # re-open short
                            otype = fdef.VOPEN
                            direct = fdef.VSHORT
                            code = self.lazyleg
                            price = self.lazyquote['bid1'] - 5.0
                            volume = 1
                            tag = 'errlazy.closeshort'
                            self.lazyerroid, doreq, rcok = self.reqorder(otype, direct, code, price, volume, tag=tag)
                    else:
                        print 'which error leg to recover?'

                    if not doreq:
                        # delay the reqorder to onNewTrade
                        self.delaytask = (otype, direct, code, price, volume, tag)
                        print 'error recovery delayed to onNewTrade'

                    oldlazystate = self.lazystate
                    oldquickstate = self.quickstate
                    oldqhold = self.qhold
                    self.lazystate = 'cancelotherERRorderring'
                    print('recover error lazy at cancelother: lazystate=%s(<-%s) quickstate=%s(<-%s) q=%d(<-%d) sprdmid=%.3f sprdfix=%.3f quickmid=%.2f, delta=%.3f' % (self.lazystate, oldlazystate, self.quickstate, oldquickstate, self.qhold, oldqhold, self.sprdmid, self.sprdmidfix, self.quickmidprice, self.delta))
                else:
                    print 'unhandled abnormallity in cancel other'

            elif self.lazystate=='cancelotherERRorderred' and o[fdef.KOID]==self.lazyerroid:
                print 'recover lazy leg fully trade'
                oldlazystate = self.lazystate
                oldquickstate = self.quickstate
                oldqhold = self.qhold
                self.lazystate = 'ready'
                self.lazyerroid = None

                print('recover error lazy traded: lazystate=%s(<-%s) quickstate=%s(<-%s) q=%d(<-%d) sprdmid=%.3f sprdfix=%.3f quickmid=%.2f, delta=%.3f' % (self.lazystate, oldlazystate, self.quickstate, oldquickstate, self.qhold, oldqhold, self.sprdmid, self.sprdmidfix, self.quickmidprice, self.delta))

            else:
                print('unexpected fully trade: lazystate=%s quickstate=%s q=%d sprdmid=%.3f sprdfix=%.3f quickmid=%.2f, delta=%.3f' % (self.lazystate, self.quickstate, self.qhold, self.sprdmid, self.sprdmidfix, self.quickmidprice, self.delta))


        self.lock.release()
        #self.logger.debug('exit OnOrderFullyTrade')

    def onCancelled(self, oid, resp):

        self.lock.acquire()
        #self.logger.debug('enter onCancelled')

        # should be lazyleg's cancel
        o, olk = self.tbook.getorder(oid)
        if o[fdef.KCODE]==self.quickleg:
            # error case
            pass
        elif o[fdef.KCODE]==self.lazyleg:
            if self.lazystate=='cancelling' or self.lazystate=='cancelother':
                # if both lazy legs are cancelled, set lazystate to ready
                oid = o[fdef.KOID]
                if oid==self.lazylegoid['ask']:
                    self.lazylegoid['ask'] = None
                elif oid==self.lazylegoid['bid']:
                    self.lazylegoid['bid'] = None

                if self.lazylegoid['bid'] is None and self.lazylegoid['ask'] is None:
                    # lazylegoid is None because traded or cancelled or not requested.
                    oldlazystate = self.lazystate
                    self.lazystate = 'ready'

                    oldquickstate = self.quickstate
                    oldqhold = self.qhold
                    print('cancelled: lazystate=%s(<-%s) quickstate=%s(<-%s) q=%d(<-%d) sprdmid=%.3f sprdfix=%.3f quickmid=%.2f, delta=%.3f' % (self.lazystate, oldlazystate, self.quickstate, oldquickstate, self.qhold, oldqhold, self.sprdmid, self.sprdmidfix, self.quickmidprice, self.delta))
            else:# include lazy setting, set, cancelotherERRxxx, etc.
                print 'abnormal order cancelled at lazystate=%s quickstate=%s' % (self.lazystate, self.quickstate)

        self.lock.release()
        #self.logger.debug('exit onCancelled')

    def onOrderRejected(self, oid, resp):
        # really urgent case, log and show error sign.
        print 'order rejected at lazystate=%s quickstate=%s' % (self.lazystate, self.quickstate)
        pass

    def onCancelRejected(self, oid, resp):

        self.lock.acquire()
        #self.logger.debug('enter onCancelRejected')

        o, olk = self.tbook.getorder(oid)
        if o[fdef.KCODE]==self.quickleg:
            # really urgent
            pass
        elif o[fdef.KCODE]==self.lazyleg:
            if self.lazystate=='cancelling' or self.lazystate=='cancelother':
                # XXX: lazystate may be also in traded/ready?
                # if it is a race condition of cancel-while-traded, then
                # go on to cancelother state and actions.
                try:
                    # a dirty hack for ctp request.
                    if o['ErrorID']==26:
                        print 'cancel failure by-pass'
                    else:
                        # urgent case
                        print 'cancel both side failed.'
                        pass
                except KeyError:
                    # urgent case
                    print 'abnormal cancel rejected for unkown reason.'
                    pass
                pass
            elif self.lazystate=='cancelother':
                # really urgent
                print 'abnormal cancel other failed'
                pass
            else:
                print 'abnormal cancel rejected at lazystate=%s quickstate=%s' % (self.lazystate, self.quickstate)

        self.lock.release()
        #self.logger.debug('exit onCancelRejected')

    def onOrderAccepted(self, oid, resp):
        self.lock.acquire()
        #self.logger.debug('enter onOrderAccepted')

        o, olk = self.tbook.getorder(oid)
        if 'OrderSysID' in o:
            # accept by ctp, skip accept by broker's front
            if oid==self.quicklegoid and self.quickstate=='orderring':
                self.quickstate = 'ordered'
                print 'quick order accepted'
            elif oid==self.lazylegoid['ask'] and self.lazystate=='setting':
                self.lazyordersetok['ask'] = True
                print 'lazy ask order accepted'
            elif oid==self.lazylegoid['bid'] and self.lazystate=='setting':
                self.lazyordersetok['bid'] = True
                print 'lazy bid order accepted'
            elif oid==self.lazyerroid and self.lazystate=='cancelotherERRorderring':
                self.lazystate = 'cancelotherERRorderred'
            else:
                print 'accept at unknown state or order at lazystate=%s quickstate=%s' % (self.lazystate, self.quickstate)

            if self.lazyordersetok['ask'] and self.lazyordersetok['bid'] and self.lazystate=='setting':
                oldlazystate = self.lazystate
                self.lazystate = 'set'
                oldquickstate = self.quickstate
                oldqhold = self.qhold
                print('lazy set ok: lazystate=%s(<-%s) quickstate=%s(<-%s) q=%d(<-%d) sprdmid=%.3f sprdfix=%.3f quickmid=%.2f, delta=%.3f' % (self.lazystate, oldlazystate, self.quickstate, oldquickstate, self.qhold, oldqhold, self.sprdmid, self.sprdmidfix, self.quickmidprice, self.delta))

        self.lock.release()
        #self.logger.debug('exit onOrderAccepted')

    def onNewTrade(self, oid, resp):
        o, olk = self.tbook.getorder(oid)
        if o[fdef.KCODE]==self.quickleg:
            self.logger.info('quick traded with %s', str(resp))
        elif o[fdef.KCODE]==self.lazyleg:
            self.logger.info('lazy traded with %s', str(resp))

        if self.delaytask is not None:
            otype, direct, code, price, volume, tag = self.delaytask
            self.lazyerroid, doreq, rcok = self.reqorder(otype, direct, code, price, volume, tag=tag)
            print 'delayed task reqed, doreq=%s, rcok=%s' % (doreq, rcok)
            self.delaytask = None


class crabconsole(stratconsole):
    def do_quit(self, args):
        if args=='FORCE':
            print 'Quitting'
            return True
        else:
            if self.top.issuspend():
                print 'Quitting'
                return True
            else:
                print 'suspend first or stop FORCE'

    def do_suspend(self, args):
        self.top.dosuspend()

    def do_resume(self, args):
        self.top.dounsuspend()

    def do_issuspend(self, args):
        print self.top.issuspend()

def main():
    try:
        mysec = sys.argv[1]
    except IndexError:
        print 'What\'s your section?'
        sys.exit(1)
    runstrat(mysec, crabstrat, crabconsole, logfnwithdate=True)

if __name__=='__main__':
    main()

# $Id$
