# scalpel 1: set limit order at bid1-0.2 and sell it at bid1 once the order is traded

import sys
import cPickle as pickle
from threading import Lock, Timer
from collections import defaultdict

from flamelib import stratconsole, runstrat, strattop
import flaredef as fdef

class scpstrat(strattop):
    def setup(self):
        self.legcode = self.mycfg['legcode']
        self.ptick = float(self.mycfg['pricetick'])
        self.tmode = self.mycfg['tmode']
        self.maxvolperorder = int(self.mycfg['maxvolperorder'])
        self.MAXCLOSETICKCNT = int(self.mycfg['maxclosetickcnt'])
        self.cancelmode = self.mycfg['cancelmode']
        self.canceltimer = float(self.mycfg['canceltimer'])
        self.minreqvol = int(self.mycfg['minreqvol'])
        self.qhold = 0
        self.state = 'ready'
        self.closetickcnt = 0
        self.oid = None
        self.quote = None
        self.lock = Lock()

        # intentially set to suspended at startup
        self.suspendflag = True

        self.pubsub.subscribe((fdef.CHQUOTE, fdef.CHHEARTBEAT))

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

    def docancel(self, oid):
        self.lock.acquire()

        if self.cancelmode=='ontimer' and self.state=='set':
            self.cancelorder(oid)
            self.state = 'cancelling'
            self.logger.info('cancel order on timer')
        else:
            self.logger.info('docancel triggered at wrong time, cancelmode=%s state=%s', self.cancelmode, self.state)

        self.lock.release()

    def signal(self, m):
        '''
        set limit buy order to bid1-0.2, once hit sell at bid1.

        OR

        set limit sell order to ask1+0.2, once hit buy at ask1.
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

                if self.state=='ready':
                    # set limit order
                    if self.tmode=='bid' and q['bidvol1']>=self.minreqvol:
                        otype = fdef.VOPEN
                        direct = fdef.VLONG
                        code = self.legcode
                        price = q['bid1'] - self.ptick
                        volume = 1
                        self.oid, doreq, rcok = self.reqorder(otype, direct, code, price, volume, tag='set')

                        self.state = 'setting'
                        self.logger.info('new quick quote %s', self.quote2str(q))
                        self.logger.info('setting bid=%.2f', price)

                    elif self.tmode=='ask' and q['askvol1']>=self.minreqvol:
                        otype = fdef.VOPEN
                        direct = fdef.VSHORT
                        code = self.legcode
                        price = q['ask1'] + self.ptick
                        volume = 1
                        self.oid, doreq, rcok = self.reqorder(otype, direct, code, price, volume, tag='set')

                        self.state = 'setting'
                        self.logger.info('new quick quote %s', self.quote2str(q))
                        self.logger.info('setting ask=%.2f, cancel %s', price, 'on next quote' if self.cancelmode=='onquote' else 'in %.2f secs'%self.canceltimer)

                    else:
                        self.logger.info('new quick quote %s', self.quote2str(q))

                elif self.state=='set':
                    # cancel existing limit order, if necessary
                    if self.cancelmode=='onquote':
                        self.cancelorder(self.oid)
                        self.state = 'cancelling'
                        self.logger.info('new quick quote %s', self.quote2str(q))
                        self.logger.info('cancel order on quote')
                    else:
                        self.logger.info('new quick quote %s', self.quote2str(q))

                elif self.state=='closing':
                    self.closetickcnt += 1
                    if self.closetickcnt >= self.MAXCLOSETICKCNT:
                        self.cancelorder(self.oid)
                        self.logger.info('new quick quote %s', self.quote2str(q))
                        self.logger.info('try cancel and force close')
                    else:
                        self.logger.info('new quick quote %s', self.quote2str(q))

                else:
                    self.logger.info('new quick quote %s', self.quote2str(q))

                self.quote = q

        self.lock.release()

    def OnOrderFullyTrade(self, oid, resp):
        # set legs states and qhold
        self.lock.acquire()

        o, olk = self.tbook.getorder(oid)
        if o[fdef.KCODE]==self.legcode:
            if self.state=='set' or self.state=='setting' or self.state=='cancelling':
                # limit order traded, close it immediatelly
                if self.tmode=='bid':
                    self.qhold += 1
                    # close long position
                    otype = fdef.VCLOSE
                    direct = fdef.VLONG
                    code = self.legcode
                    price = o[fdef.KPRICE] + self.ptick
                    volume = 1
                    self.oid, doreq, rcok = self.reqorder(otype, direct, code, price, volume, force=True, tag='close')
                    self.state = 'closing'
                    self.closetickcnt = 0
                    self.logger.info('closing bid @ %.2f', price)
                elif self.tmode=='ask':
                    self.qhold -= 1
                    otype = fdef.VCLOSE
                    direct = fdef.VSHORT
                    code = self.legcode
                    price = o[fdef.KPRICE] - self.ptick
                    volume = 1
                    self.oid, doreq, rcok = self.reqorder(otype, direct, code, price, volume, force=True, tag='close')
                    self.closetickcnt = 0
                    self.state = 'closing'
                    self.logger.info('closing ask @ %.2f', price)

            elif self.state=='closing' or self.state=='forceclosing':
                # position closed, return to ready
                if self.tmode=='bid':
                    self.qhold -= 1
                    self.state = 'ready'
                    self.logger.info('bid closed')
                elif self.tmode=='ask':
                    self.qhold += 1
                    self.state = 'ready'
                    self.logger.info('ask closed')

            else:
                self.logger.error('unexpected state %s', self.state)
                self.logger.error('resp %s', str(resp))
                print 'unexpected state=%s' % self.state

        self.lock.release()

    def onCancelled(self, oid, resp):
        # cancel can only happen from other sources such as Q7
        self.lock.acquire()

        o, olk = self.tbook.getorder(oid)
        if o[fdef.KCODE]==self.legcode:
            if self.state=='cancelling':
                # limit order cancelled, return to ready
                self.state = 'ready'
                self.logger.info('limit order cancelled')
            elif self.state=='closing':
                if self.tmode=='bid':
                    otype = fdef.VCLOSE
                    direct = fdef.VLONG
                    code = self.legcode
                    price = self.quote['bid1'] - 5.0
                    volume = 1
                    self.oid, doreq, rcok = self.reqorder(otype, direct, code, price, volume, tag='forceclose')
                    self.state = 'forceclosing'
                    self.logger.info('force closing')

                elif self.tmode=='ask':
                    otype = fdef.VCLOSE
                    direct = fdef.VSHORT
                    code = self.legcode
                    price = self.quote['ask1'] + 5.0
                    volume = 1
                    self.oid, doreq, rcok = self.reqorder(otype, direct, code, price, volume, tag='forceclose')
                    self.state = 'forceclosing'
                    self.logger.info('force closing')

            else:
                self.logger.error('unexpected state %s', self.state)
                self.logger.error('resp %s', str(resp))
                print 'unexpected state=%s' % self.state

        self.lock.release()

    def onOrderRejected(self, oid, resp):
        # rare exception case
        o, olk = self.tbook.getorder(oid)
        self.logger.error('order rejected %s', o)
        self.logger.error('resp %s', str(resp))
        print 'order rejected'

    def onCancelRejected(self, oid, resp):
        # rare case
        self.lock.acquire()

        o, olk = self.tbook.getorder(oid)
        if o[fdef.KCODE]==self.legcode:
            if self.state=='cancelling' or self.state=='closing':
                # limit order cancel failed, maybe it is already traded,
                # otherwise it is an exception case
                try:
                    if o['ErrorID']==26:
                        # order already traded.
                        pass
                    else:
                        # urgent case
                        self.logger.error('unexpected state %s', self.state)
                        self.logger.error('resp %s', str(resp))
                        print 'unexpected state=%s' % self.state
                except KeyError:
                    # urgent case
                    self.logger.error('unexpected state %s', self.state)
                    self.logger.error('resp %s', str(resp))
                    print 'unexpected state=%s' % self.state
            else:
                self.logger.error('unexpected state %s', self.state)
                self.logger.error('resp %s', str(resp))
                print 'unexpected state=%s' % self.state

        self.lock.release()

    def onOrderAccepted(self, oid, resp):
        self.lock.acquire()

        o, olk = self.tbook.getorder(oid)
        if o[fdef.KCODE]==self.legcode:
            if self.state=='setting':
                # limit order acceptted
                self.state = 'set'
                self.logger.info('order set')
                if self.cancelmode=='ontimer':
                    tcancel = Timer(self.canceltimer, self.docancel, [self.oid])
                    tcancel.start()

            elif self.state=='cancelling' or self.state=='set' or self.state=='closing' or self.state=='forceclosing':
                pass
            else:
                self.logger.error('unexpected state %s', self.state)
                self.logger.error(str(resp))
                print 'unexpected state=%s' % self.state

        self.lock.release()
    
    def onNewTrade(self, oid, resp):
        # log trade info
        o, olk = self.tbook.getorder(oid)
        if o[fdef.KTAG]=='set':
            self.logger.info('limit order traded price=%.2f', resp[fdef.KPRICE])
        elif o[fdef.KTAG]=='close':
            self.logger.info('close order traded price=%.2f', resp[fdef.KPRICE])
        elif o[fdef.KTAG]=='forceclose':
            self.logger.info('close order traded price=%.2f force=yes', resp[fdef.KPRICE])

class scpconsole(stratconsole):
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
    runstrat(mysec, scpstrat, scpconsole, logfnwithdate=True)

if __name__=='__main__':
    main()

# $Id$
