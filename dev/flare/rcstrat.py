# a risk-checking strategy, which also test engine.

import os, sys

from flamelib import stratconsole, runstrat, strattop
import flaredef as fdef
import config

class rcstrat(strattop):
    def setup(self):
        self.mycfg['maxvolperorder'] = int(self.mycfg['maxvolperorder'])

        chresp = fdef.fullname(fdef.CHORESP, self.strat)
        self.pubsub.subscribe((chresp, fdef.CHQUOTE, fdef.CHHEARTBEAT))
        return True

    def riskcheck(self, oid):
        o, olk = self.tbook.getorder(oid)
        ret = False
        if o is not None:
            with olk:
                vol = o[fdef.KVOLUME]
                if vol <= self.mycfg['maxvolperorder']:
                    ret = True
                else:
                    ret = False
        self.logger.debug('order %s rc result: %s', oid, ret)
        return ret

class rcconsole(stratconsole):
    def __init__(self, top):
        stratconsole.__init__(self, top)
        self.lastoid = None

    def do_lastoid(self, args):
        print self.lastoid

    def do_order(self, args):
        tp = args.split()
        if len(tp) > 0:
            self.top.tbook.printorder(tp[0])
        else:
            self.top.tbook.printorder(self.lastoid)

    def do_cancel(self, args):
        tp = args.split()
        try:
            self.top.cancelorder(tp[0])
        except IndexError:
            self.top.cancelorder(self.lastoid)

    def do_open(self, args):
        tp = args.split()
        otype = fdef.VOPEN
        direct = tp[0].upper()
        code = tp[1].upper()
        price = float(tp[2])
        volume = int(tp[3])
        force = (tp[4]=='force')
        try:
            cancelimmd = int(tp[5])
        except IndexError:
            cancelimmd = 0

        lastoid, doreq, rcok = self.top.reqorder(otype, direct, code, price, volume, force=force)
        print 'requested,' if (doreq or force) else 'unrequested,', 'riskcheck ok,' if (doreq and rcok) else 'riskcheck failed,', lastoid
        self.lastoid = lastoid

        if cancelimmd and doreq:
            self.top.cancelorder(self.lastoid)
            print '%s cancelled immediately' % self.lastoid

    def do_close(self, args):
        tp = args.split()
        otype = fdef.VCLOSE
        direct = tp[0].upper()
        code = tp[1].upper()
        price = float(tp[2])
        volume = int(tp[3])
        force = (tp[4]=='force')
        try:
            cancelimmd = int(tp[5])
        except IndexError:
            cancelimmd = 0

        lastoid, doreq, rcok = self.top.reqorder(otype, direct, code, price, volume, force=force)
        print 'requested,' if (doreq or force) else 'unrequested,', 'riskcheck ok,' if (doreq and rcok) else 'riskcheck failed,', lastoid
        self.lastoid = lastoid

        if cancelimmd and doreq:
            self.top.cancelorder(self.lastoid)
            print '%s cancelled immediately' % self.lastoid

def main():
    mysec = 'rcstrat'
    runstrat(mysec, rcstrat, rcconsole)

if __name__=='__main__':
    main()
    sys.exit(1)
# $Id$ 
