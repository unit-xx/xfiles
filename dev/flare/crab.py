# CalendaR ARbitrage.

import sys
import cPickle as pickle
from threading import Thread, Lock
from math import floor, ceil
from collections import defaultdict

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
        self.sprdmid = 0.0
        self.sprdmidfix = 0.0

        self.lazylegoid = {
                'ask':None,
                'bid':None
                }
        self.lazyordersetok = {
                'ask':False,
                'bid':False
                }
        self.quicklegoid = None

        self.quickmidprice = 0.0

        self.quickstate = 'ready'
        self.lazystate = 'ready'
        self.sprdaskmode = 'empty'
        self.sprdbidmode = 'empty'

        self.lock = Lock()

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
        self.logger.debug('order %s rc result: %s', oid, ret)
        return ret

    def floor02(self, x):
        return 0.2*floor(x/0.2)

    def ceil02(self, x):
        return 0.2*ceil(x/0.2)

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

        isresetlazy = False

        if m['channel'] == fdef.CHQUOTE:
            try:
                q = pickle.loads(m['data'])
            except:
                return

            # if midprice of quickleg is changed, reset lazyleg order
            if q['code'] == self.quickleg:
                newquickmid = (q['bid1'] + q['ask1'])/2
                if newquickmid != self.quickmidprice:
                    self.shortmidprice = newquickmid
                    isresetlazy = True

        elif m['channel'] == self.chma:
            try:
                inst, tickunit, maval = pickle.loads(m['data'])
            except:
                return

            if inst==self.quickleg or inst==self.lazyleg:
                midprice[inst]['ticku'] = tickunit
                midprice[inst]['value'] = maval
                try:
                    # if midprice of sprd is changed, reset lazyleg order
                    if midprice[self.quickleg]['ticku']==midprice[self.lazyleg]['ticku']:
                        newsprdmid = midprice[self.lazyleg]['value'] - midprice[self.quickleg]['value']
                        if newsprdmid != self.sprdmid:
                            self.sprdmid = newsprdmid
                            self.sprdmidfix = self.sprdmid - self.qhold * self.sigma
                            isresetlazy = True

                except KeyError:
                    # ma hasn't been received for some legs.
                    pass
                except TypeError:
                    # ma is none since not enough quotes is accumulated to calc ma
                    pass

        if self.lazystate=='ready' and self.quickstate=='ready':
            # set limit order of lazyleg
            lazyask = self.sprdmidfix + self.quickmidprice + self.delta
            lazybid = self.sprdmidfix + self.quickmidprice - self.delta
            lazyask = self.ceil02(lazyask)
            lazybid = self.floor02(lazybid)

            if q==0:
                self.sprdaskmode = 'openshort'
                self.sprdbidmode = 'openlong'
            elif q > 0:
                self.sprdaskmode = 'closelong'
                self.sprdbidmode = 'openlong'
            elif q < 0:
                self.sprdaskmode = 'openshort'
                self.sprdbidmode = 'closeshort'

            if q==self.qmax:
                self.sprdbidmode = 'empty'
            elif q==-self.qmax:
                self.sprdaskmode = 'empty'

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
                self.lazyordersetok['ask'] = False
                # urgent case if doreq is False
            elif self.sprdaskmode=='closelong':
                otype = fdef.VCLOSE
                direct = fdef.VLONG
                code = self.lazyleg
                price = lazyask
                volume = 1
                askoid, doreq, rcok = self.reqorder(otype, direct, code, price, volume)
                self.lazyordersetok['ask'] = False
                # urgent case if doreq is False
            else:
                # empty
                self.lazyordersetok['ask'] = True
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
                self.lazyordersetok['bid'] = False
                # urgent case if doreq is False
            elif self.sprdbidmode=='closeshort':
                otype = fdef.VCLOSE
                direct = fdef.VSHORT
                code = self.lazyleg
                price = lazybid
                volume = 1
                bidoid, doreq, rcok = self.reqorder(otype, direct, code, price, volume)
                self.lazyordersetok['bid'] = False
                # urgent case if doreq is False
            else:
                # empty
                self.lazyordersetok['bid'] = True
                pass
            self.lazylegoid['bid'] = bidoid

            oldlazystate = self.lazystate
            oldquickstate = self.quickstate
            oldqhold = self.qhold
            self.lazystate = 'setting'

            print('set lazy limit: lazystate=%s(<-%s) quickstate=%s(<-%s) q=%d(<-%d) sprdmid=%.3f sprdfix=%.3f quickmid=%.2f, delta=%.3f lazyask=%.2f lazybid=%.2f ' % (self.lazystate, oldlazystate, self.quickstate, oldquickstate, self.qhold, oldqhold, self.sprdmid, self.sprdmidfix, self.quickmidprice, self.delta, lazyask, lazybid))

        elif self.lazystate=='set' and isresetlazy:
            # NOTE: change qhold while lazy and short are both traded
            # NOTE: when q=qmax/-qmax, cancel other lazy is different
            # NOTE: lock between top and bottom
            # cancel first
            if self.lazylegoid['ask'] is not None:
                self.cancelorder(self.lazylegoid['ask'])

            if self.lazylegoid['bid'] is not None:
                self.cancelorder(self.lazylegoid['bid'])

            oldlazystate = self.lazystate
            oldquickstate = self.quickstate
            oldqhold = self.qhold
            self.lazystate = 'cancelling'

            print('cancel both lazy limit lazystate=%s(<-%s) quickstate=%s(<-%s) q=%d(<-%d) sprdmid=%.3f sprdfix=%.3f quickmid=%.2f, delta=%.3f lazyask=%.2f lazybid=%.2f ' % (self.lazystate, oldlazystate, self.quickstate, oldquickstate, self.qhold, oldqhold, self.sprdmid, self.sprdmidfix, self.quickmidprice, self.delta, lazyask, lazybid))

        self.lock.release()

    def OnOrderFullyTrade(self, oid, resp):

        self.lock.acquire()

        # whose order? lazyleg or quickleg?
        o, olk = self.tbook.getorder(oid)
        if o[fdef.KCODE]==self.quickleg:
            # quickleg should be in 'ordered' state
            # set quickleg state to ready
            lazyotype = o[fdef.KOTYPE]
            lazydirect = fdef.VSHORT if o[fdef.KDIR]==fdef.VLONG else fdef.VLONG
            if (lazyotype==fdef.VOPEN and lazydirect==fdef.VSHORT) or (lazyotype==fdef.VCLOSE and lazydirect==fdef.VLONG):
                # sprd ask side is traded
                self.qhold = self.qhold - 1
            else:
                # sprd bid side is traded
                self.qhold = self.qhold + 1

            oldlazystate = self.lazystate
            oldquickstate = self.quickstate
            oldqhold = self.qhold
            self.quickstate = 'ready'
            self.sprdmidfix = self.sprdmid - self.qhold * self.sigma

            print('quick traded: lazystate=%s(<-%s) quickstate=%s(<-%s) q=%d(<-%d) sprdmid=%.3f sprdfix=%.3f quickmid=%.2f, delta=%.3f lazyask=%.2f lazybid=%.2f ' % (self.lazystate, oldlazystate, self.quickstate, oldquickstate, self.qhold, oldqhold, self.sprdmid, self.sprdmidfix, self.quickmidprice, self.delta, lazyask, lazybid))

        elif o[fdef.KCODE]==self.lazyleg:
            # lazyleg should be in 'set' state
            # lazyleg to cancelother state
            # cancel other lazyleg
            if self.lazystate=='set':
                if oid==self.lazylegoid['ask']:
                    # ask side traded, cancel bid side
                    self.lazylegoid['ask'] = None
                    if self.lazylegoid['bid'] is not None:
                        self.cancelorder(self.lazylegoid['bid'])
                elif oid==self.lazylegoid['bid']:
                    self.lazylegoid['bid'] = None
                    if self.lazylegoid['ask'] is not None:
                        self.cancelorder(self.lazylegoid['ask'])

                if self.lazylegoid['ask'] is None and self.lazylegoid['bid'] is None:
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
                price = -1.0 # market price
                volume = 1
                quickoid, doreq, rcok = self.reqorder(otype, direct, code, price, volume)
                self.quicklegoid = quickoid
                oldquickstate = self.quickstate
                self.quickstate = 'orderring'

                oldqhold = self.qhold
                print('cancel other lazy: lazystate=%s(<-%s) quickstate=%s(<-%s) q=%d(<-%d) sprdmid=%.3f sprdfix=%.3f quickmid=%.2f, delta=%.3f lazyask=%.2f lazybid=%.2f ' % (self.lazystate, oldlazystate, self.quickstate, oldquickstate, self.qhold, oldqhold, self.sprdmid, self.sprdmidfix, self.quickmidprice, self.delta, lazyask, lazybid))
            elif self.lazystate=='cancelling':
                # cancel-while-traded race condition.
                if oid==self.lazylegoid['ask']:
                    # ask side traded, cancel bid side
                    self.lazylegoid['ask'] = None
                elif oid==self.lazylegoid['bid']:
                    self.lazylegoid['bid'] = None

                if self.lazylegoid['ask'] is None and self.lazylegoid['bid'] is None:
                    oldlazystate = self.lazystate
                    self.lazystate = 'ready'
                else:
                    oldlazystate = self.lazystate
                    self.lazystate = 'cancelother'

                # order quick leg
                otype = o[fdef.KOTYPE]
                direct = fdef.VSHORT if o[fdef.KDIR]==fdef.VLONG else fdef.VLONG
                code = self.quickleg
                price = -1.0 # market price
                volume = 1
                quickoid, doreq, rcok = self.reqorder(otype, direct, code, price, volume)
                self.quicklegoid = quickoid
                oldquickstate = self.quickstate
                self.quickstate = 'orderring'

                oldqhold = self.qhold
                print('cancel other lazy: lazystate=%s(<-%s) quickstate=%s(<-%s) q=%d(<-%d) sprdmid=%.3f sprdfix=%.3f quickmid=%.2f, delta=%.3f lazyask=%.2f lazybid=%.2f ' % (self.lazystate, oldlazystate, self.quickstate, oldquickstate, self.qhold, oldqhold, self.sprdmid, self.sprdmidfix, self.quickmidprice, self.delta, lazyask, lazybid))

        self.lock.release()

    def onCancelled(self, oid, resp):

        self.lock.acquire()

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
                    oldlazystate = self.lazystate
                    self.lazystate = 'ready'

            oldlazystate = self.lazystate
            oldquickstate = self.quickstate
            oldqhold = self.qhold
            print('lazystate=%s(<-%s) quickstate=%s(<-%s) q=%d(<-%d) sprdmid=%.3f sprdfix=%.3f quickmid=%.2f, delta=%.3f lazyask=%.2f lazybid=%.2f ' % (self.lazystate, oldlazystate, self.quickstate, oldquickstate, self.qhold, oldqhold, self.sprdmid, self.sprdmidfix, self.quickmidprice, self.delta, lazyask, lazybid))

        self.lock.release()

    def onOrderRejected(self, oid, resp):
        # really urgent case, log and show error sign.
        print 'order rejected.'
        pass

    def onCancelRejected(self, oid, resp):

        self.lock.acquire()

        o, olk = self.tbook.getorder(oid)
        if o[fdef.KCODE]==self.quickleg:
            # really urgent
            pass
        elif o[fdef.KCODE]==self.lazyleg:
            if self.lazystate=='cancelling':
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
                    print 'failed for unkown reason.'
                    pass
                pass
            elif self.lazystate=='cancelother':
                # really urgent
                print 'cancel other failed'
                pass

        self.lock.release()

    def onOrderAccepted(self, oid, resp):
        self.lock.acquire()

        o, olk = self.tbook.getorder(oid)
        if 'OrderSysID' in o:
            if oid==self.lazylegoid['ask']:
                self.lazyordersetok['ask'] = True
            elif oid==self.lazylegoid['bid']:
                self.lazyordersetok['bid'] = True
            elif oid==self.quicklegoid:
                self.quickstate = 'ordered'

            if self.lazyordersetok['ask'] and lazyordersetok['bid']:
                self.lazystate = 'set'

        self.lock.release()

class crabconsole(stratconsole):
    pass

def main():
    mysec = 'crabstrat'
    runstrat(mysec, crabstrat, crabconsole)

if __name__=='__main__':
    main()

# $Id$
