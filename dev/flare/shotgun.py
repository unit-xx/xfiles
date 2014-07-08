# canlendar arbitrage with simultaneous shot.


from flamelib import stratconsole, runstrat, strattop
import flaredef as fdef
import config

class shotstrat(strattop):
    def setup(self):
        self.chma = self.mycfg['machannel']
        self.maxvolperorder = int(self.mycfg['maxvolperorder'])

        self.quickleg = self.mycfg['quickleg']
        self.lazyleg = self.mycfg['lazyleg']
        self.sigma = float(self.mycfg['sigma'])
        self.intensity = float(self.mycfg['intensity'])
        self.delta = self.intensity + self.sigma/2
        self.qmax = int(self.mycfg['qmax'])

        self.midprice = defaultdict(dict)
        self.quickquote = None
        self.lazyquote = None
        self.qhold = 0
        self.sprdmid = None
        self.sprdmidfix = None

        self.sprdbid = None
        self.sprdask = None

        self.quickstate = 'ready'
        self.lazystate = 'ready'
        self.shotstate = 'ready'
        self.shotdir = 'empty'

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
    
    def issuspend(self):
        return (self.suspendflag==True and self.qhold==0 and self.lazystate=='ready' and self.quickstate=='ready')
    
    def dosuspend(self):
        self.suspendflag = True

    def dounsuspend(self):
        self.suspendflag = False

    def signal(self, m):
        '''
        calender spread has 'ask' and 'bid' prices.

        Once spread ask is low enough, then buy spread (q=q+1)
        Once spread bid is high enough, then sell spread (q=q-1)
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

            if q['code'] == self.quickleg:
                if q['bid1']>q['upperlimit'] or q['bid1']<q['lowerlimit'] or q['ask1']>q['upperlimit'] or q['ask1']<q['lowerlimit']:
                    pass
                else:
                    self.quickquote = q
                    self.logger.info('new quick quote %s', self.quote2str(q))
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
            # fire shots if necessary
            if self.sprdbid > self.sprdmidfix + self.delta:
                if self.qhold > -self.qmax:
                    # do sell
                    self.shotstate = 'shotting'
                    self.lazystate = 'shotting'
                    self.quickstate = 'shotting'
                    self.shotdir = 'sell'
            elif self.sprdask < self.sprdmidfix - self.delta:
                if self.qhold < self.qmax:
                    # dobuy
                    self.shotstate = 'shotting'
                    self.lazystate = 'shotting'
                    self.quickstate = 'shotting'
                    self.shotdir = 'buy'
                    pass

    def OnOrderFullyTrade(self, oid, resp):
        # set legs states and qhold
        o, olk = self.tbook.getorder(oid)
        if o[fdef.KCODE]==self.quickleg:
            self.quickstate = 'ready'
        elif o[fdef.KCODE]==self.lazyleg:
            self.lazystate = 'ready'

        if self.shotstate=='shotting':
            if self.lazystate=='ready' and self.quickstate=='ready':
                self.shotstate = 'ready'
                if shotdir == 'sell':
                    self.qhold -= 1
                else:
                    self.qhold += 1

    def onCancelled(self, oid, resp):
        # cancel can only happen from other sources such as Q7
        o, olk = self.tbook.getorder(oid)
        if o[fdef.KCODE]==self.quickleg:
            self.quickstate = 'cancelled'
        elif o[fdef.KCODE]==self.lazyleg:
            self.lazystate = 'cancelled'

    def onOrderRejected(self, oid, resp):
        # rare case
        o, olk = self.tbook.getorder(oid)
        self.logger.error('order rejected %s', o)

    def onCancelRejected(self, oid, resp):
        # rare case
        o, olk = self.tbook.getorder(oid)
        self.logger.error('cancel rejected %s', o)

    def onOrderAccepted(self, oid, resp):
        # set legs states
        pass
    
    def onNewTrade(self, oid, resp):
        # log trade info
        o, olk = self.tbook.getorder(oid)
        if o[fdef.KCODE]==self.quickleg:
            self.logger.info('quick traded with %s', str(resp))
        elif o[fdef.KCODE]==self.lazyleg:
            self.logger.info('lazy traded with %s', str(resp))

class shotconsole(stratconsole):
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
    runstrat(mysec, shotstrat, shotconsole)

if __name__=='__main__':
    main()
    
# $Id$
