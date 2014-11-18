# taf: test-and-follow. Always queue at the end of bid1/ask1, when hit, trend following at the downward/upward direction.

import sys
import cPickle as pickle
from threading import Lock, Timer
from collections import defaultdict

from flamelib import stratconsole, runstrat, strattop
import flaredef as fdef

class followstrat(strattop):
    def setup(self):
        # TODO: maintain order state, track pnl/dd
        # key=oid, value=dict(dir, oprice, maxdd, maxprofit, maxloss, ...)
        self.orders = {}
        self.trackingopen = []
        self.quote = None
        self.lock = Lock()

        # intentially set to suspended at startup
        self.suspendflag = True

        self.pubsub.subscribe((fdef.CHQUOTE, fdef.CHHEARTBEAT, fdef.CHFOLLOW))

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
    
    def issuspend(self):
        return (self.suspendflag==True and self.qhold==0 and self.state=='ready')
    
    def dosuspend(self):
        self.suspendflag = True

    def dounsuspend(self):
        self.suspendflag = False

    def quote2str(self, q):
        keys = ('code', 'ask1', 'askvol1', 'bid1', 'bidvol1', 'time', 'msec', 'tic')
        fmt = ('s', '.2f', 'd', '.2f', 'd', 's', 'd', '.2f')
        
        fmt = ['%%(%s)%s'%(x[0],x[1]) for x in zip(keys, fmt)]

        s = ' '.join([' '.join(x) for x in zip(keys, fmt)])
        return s % q

    def signal(self, m):
        '''
        receive follow signal and do it.
        '''
        self.lock.acquire()

        if m['channel'] == fdef.CHQUOTE:
            try:
                q = pickle.loads(m['data'])
            except:
                print 'quote unpickling failed.'
                self.lock.release()
                #self.logger.debug('exit signal')
                return

            if q['code'] == self.legcode:

                if self.issuspend():
                    self.logger.info('new quick quote %s', self.quote2str(q))
                    self.lock.release()
                    return
                else:
                    # update pnl and dd for active orders
                    toclose = []
                    for oid in self.trackingopen:
                        orec = self.orders[oid]
                        if orec['stae']=='opened':
                            orec['pnl'] = orec['tdir'] * (q['last']-orec['refoprice'])
                            if (orec['pnl']-orec['maxpnl'] > 1e-3):
                                orec['maxpnl'] = orec['pnl']

                            orec['dd'] = orec['pnl'] - orec['maxpnl']

                            # stop profit
                            if (orec['pnl']-orec['maxprofit']>1e-3):
                                toclose.append(oid)
                            # stop loss
                            elif (orec['pnl']-orec['maxloss']<1e-3):
                                toclose.append(oid)

                            # stop on max dd
                            if (orec['dd']-orec['maxdd']<1e-3):
                                toclose.append(oid)

                    for ooid in toclose:
                        oorec = self.orders[ooid]
                        tdir = orec['tdir']

                        otype = fdef.VCLOSE
                        direct = fdef.VLONG if (tdir>0) else fdef.VSHORT
                        price = (self.quote['ask1']+2) if (tdir<0) else (self.quote['bid1']-2)
                        volume = 1
                        coid, doreq, rcok = self.reqorder(otype, direct, code, price, volume, tag='close')
                        if doreq:
                            oorec['state'] = 'closing'
                            oorec['coid'] = coid

                            corec = {}
                            corec['oid'] = coid
                            corec['ooid'] = ooid
                        else:
                            self.logger.erro('close not requested')

                self.quote = q

        elif m['channel'] == fdef.CHFOLLOW:
            try:
                followparam = pickle.loads(m['data'])
            except:
                print 'follow signal unpickling failed.'
                self.lock.release()
                #self.logger.debug('exit signal')
                return

            code = followparam['code']
            refoprice = followparam['refoprice']
            maxloss = followparam['maxloss']
            maxprofit = followparam['maxprofit']
            maxdd = followparam['maxdd']
            tdir = followparam['tdir']

            if code!=self.legcode:
                self.lock.release()
                self.logger.warning('mismatched contract code')
                print('mismatched contract code')
                return
            else:
                otype = fdef.VOPEN
                direct = fdef.VLONG if (tdir>0) else fdef.VSHORT
                price = (self.quote['ask1']+2) if (tdir>0) else (self.quote['bid1']-2)
                volume = 1
                oid, doreq, rcok = self.reqorder(otype, direct, code, price, volume, tag='open')

                if doreq:
                    orec = {}
                    orec['oid'] = oid
                    orec['tdir'] = tdir
                    orec['otype'] = otype
                    orec['refoprice'] = refoprice
                    orec['pnl'] = 0.0
                    orec['maxpnl'] = 0.0
                    orec['maxprofit'] = maxprofit
                    orec['maxloss'] = maxloss
                    orec['maxdd'] = maxdd
                    orec['state'] = 'requested'
                    self.orders[oid] = orec
                    self.trackingopen.append(oid)

        self.lock.release()

    def OnOrderFullyTrade(self, oid, resp):
        # set legs states and qhold
        self.lock.acquire()

        o, olk = self.tbook.getorder(oid)
        orec = self.orders[oid]
        if (orec['otype']==fdef.VOPEN):
            orec['state'] = 'opened'
        elif (orec['otype']==fdef.VCLOSE):
            openoid = orec['ooid']
            orec['state'] = 'closed'
            self.trackingopen.remove[openoid]

        self.lock.release()

    def onCancelled(self, oid, resp):
        # cancel can only happen from other sources such as Q7
        self.lock.acquire()

        o, olk = self.tbook.getorder(oid)
        if oid in self.trackingopen:
            self.logger.error('open order cancelled')
            self.trackingopen.remove(oid)
        else:
            self.logger.error('close order cancelled')
            self.trackingclose.remove(oid)

        self.lock.release()

    def onOrderRejected(self, oid, resp):
        # rare exception case
        self.lock.acquire()

        o, olk = self.tbook.getorder(oid)
        if oid in self.trackingopen:
            self.logger.error('open order rejected')
            self.trackingopen.remove(oid)
        else:
            self.logger.error('close order rejected')
            self.trackingclose.remove(oid)

        self.lock.release()

    def onCancelRejected(self, oid, resp):
        # rare case
        self.lock.acquire()

        self.logger.error('cancel order rejected')

        self.lock.release()

    def onOrderAccepted(self, oid, resp):
        pass

    def onNewTrade(self, oid, resp):
        # log trade info
        pass

class followconsole(stratconsole):
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

    def do_qhold(self, args):
        print self.top.qhold

    def do_state(self, args):
        print self.top.state

def main():
    try:
        mysec = sys.argv[1]
    except IndexError:
        print 'What\'s your section?'
        sys.exit(1)
    runstrat(mysec, folowstrat, followconsole, logfnwithdate=True)

if __name__=='__main__':
    main()

# $Id: scp.py 922 2014-08-07 07:29:56Z gaochongnan@gmail.com $
