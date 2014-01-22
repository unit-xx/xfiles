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

        self.sigma = float(self.mycfg['sigma'])
        self.intensity = float(self.mycfg['intensity'])
        self.qmax = int(self.mycfg['qmax'])
        self.quickleg = self.mycfg['quickleg']
        self.lazyleg = self.mycfg['lazyleg']

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
        self.shortmidprice = 0.0
        
        self.mystate = 'init'
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

        if m['channel'] == fdef.CHQUOTE:
            try:
                q = pickle.loads(m['data'])
            except:
                return

            if q['code'] == self.quickleg:
                newshortmid = (q['bid1'] + q['ask1'])/2
                if newshortmid != self.shortmidprice:
                    # XXX: cancel existing lazyleg orders
                    self.shortmidprice = newshortmid

                # XXX: reset lazyleg limit orders

        elif m['channel'] == self.chma:
            # q = (inst, tu, maval)
            try:
                inst, tickunit, maval = pickle.loads(m['data'])
            except:
                return

            if inst==self.quickleg or inst==self.lazyleg:
                midprice[inst]['ticku'] = tickunit
                midprice[inst]['value'] = maval
                try:
                    if midprice[self.quickleg]['ticku']==midprice[self.lazyleg]['ticku']:
                        newsprdmid = midprice[self.lazyleg]['value'] - midprice[self.quickleg]['value']
                        if newsprdmid != self.sprdmid:
                            # XXX: cancel existing lazyleg orders
                            self.sprdmid = newsprdmid
                            self.sprdmidfix = self.sprdmid - self.qhold * self.sigma

                except KeyError:
                    # ma hasn't been received for some legs.
                    pass
                except TypeError:
                    # ma is none since not enough quotes is accumulated to calc ma
                    pass

    def onOrderRejected(self, oid, resp):
        # really urgent case
        pass

    def OnOrderFullyTrade(self, oid, resp):
        # whose order? lazyleg or quickleg?
        pass

    def onCancelRejected(self, oid, resp):
        # really urgent case
        pass

    def onCancelled(self, oid, resp):
        # should be lazyleg's cancel
        pass

class crabconsole(stratconsole):
    pass

def main():
    mysec = 'crabstrat'
    runstrat(mysec, crabstrat, crabconsole)

if __name__=='__main__':
    main()

# $Id$
