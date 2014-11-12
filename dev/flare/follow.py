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
        self.qhold = 0
        self.state = 'ready'
        # key=oid, value=dict(dir, oprice, maxdd, maxwin, maxloss, ...)
        self.order = {}
        self.openorders = []
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

                if self.state=='ready':
                    otype = fdef.VOPEN
                    direct = fdef.VLONG
                    code = self.legcode
                    price = q['bid1'] - self.ptick
                    volume = 1
                    self.oid, doreq, rcok = self.reqorder(otype, direct, code, price, volume, tag='set')

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
        self.lock.release()

    def onCancelled(self, oid, resp):
        # cancel can only happen from other sources such as Q7
        self.lock.acquire()

        o, olk = self.tbook.getorder(oid)
        if o[fdef.KCODE]==self.legcode:
            if self.state=='cancelling':
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
