# CalendaR ARbitrage.

import sys
import cPickle as pickle
from threading import Thread

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
        self.qmax = int(self.mycfg['qmax'])

        # using MA value to calc midprice of spread
        # store ticku and value for each leg.
        self.midprice = defaultdict(dict)
        self.sprdmid = 0.0
        self.sprdmidfix = 0.0
        self.qhold = 0

        self.lazylegoid = {
                'short':None,
                'long':None
                }
        self.quicklegoid = None

        self.quickmidprice = 0.0

        self.quickstate = 'ready'
        self.lazystate = 'ready'

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
                    self.shortmidprice = newshortmid
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
                            # XXX: cancel existing lazyleg orders
                            self.sprdmid = newsprdmid
                            self.sprdmidfix = self.sprdmid - self.qhold * self.sigma
                            isresetlazy = True

                except KeyError:
                    # ma hasn't been received for some legs.
                    pass
                except TypeError:
                    # ma is none since not enough quotes is accumulated to calc ma
                    pass

        if isresetlazy:
            if self.lazystate=='ready' and self.quickstate=='ready':
                # set limit order of lazyleg
                self.lazystate = 'setting'
                pass
            elif self.lazystate=='set':
                # cancel first

    def OnOrderFullyTrade(self, oid, resp):
        # whose order? lazyleg or quickleg?
        o, olk = self.tbook.getorder(oid)
        if o[fdef.KCODE]==self.quickleg:
            # quickleg should be in 'ordered' state
            # set quickleg state to ready
            pass
        elif o[fdef.KCODE]==self.lazyleg:
            # lazyleg should be in 'set' state
            # lazyleg to cancelother state
            # cancel other lazyleg
            # quick leg should in ready state, otherwise it is urgent
            # order quick leg
            pass

    def onCancelled(self, oid, resp):
        # should be lazyleg's cancel
        o, olk = self.tbook.getorder(oid)
        if o[fdef.KCODE]==self.quickleg:
            # error case
            pass
        elif o[fdef.KCODE]==self.lazyleg:
            if self.lazystate=='cancelling':
                # if both lazy legs are cancelled, set lazystate to ready
                pass
            elif self.lazystate=='cancelother':
                # lazy leg state -> ready
                pass

    def onOrderRejected(self, oid, resp):
        # really urgent case, log and show error sign.
        pass

    def onCancelRejected(self, oid, resp):
        o, olk = self.tbook.getorder(oid)
        if o[fdef.KCODE]==self.quickleg:
            # really urgent
            pass
        elif o[fdef.KCODE]==self.lazyleg:
            if self.lazystate=='cancelling':
                # if it is a race condition of cancel-while-traded, then
                # go on to cancelother state and actions.
                pass
            elif self.lazystate=='cancelother':
                # really urgent
                pass

class crabconsole(stratconsole):
    pass

def main():
    mysec = 'crabstrat'
    runstrat(mysec, crabstrat, crabconsole)

if __name__=='__main__':
    main()

# $Id$
