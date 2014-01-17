# a risk-checking strategy, which also test engine.

import os, sys

from flamelib import strattop, stratbottom, getstore, getpubsub, TBookCache, TBookLib, TBookProxy, stratconsole
import flaredef as fdef
import config
from util import Record

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
        stratconsole.__init__(top)
        self.lastoid = None

    def do_cancel(self, args):
        tp = args.split()
        try:
            self.top.cancelorder(tp[0])
        except IndexError:
            self.top.cancelorder(lastoid)

    def do_open(self, args):
        tp = args.split()
        otype = 'open'
        direct = tp[0].upper()
        code = tp[1].upper()
        price = float(tp[2])
        volume = int(tp[3])
        lastoid, doreq, rcok = rc.reqorder(otype, direct, code, price, volume)
        print 'requested,' if doreq else 'unrequested,', 'riskcheck ok,' if (doreq and rcok) else 'riskcheck failed,', lastoid
        self.lastoid = lastoid

    def do_close(self, args):
        tp = args.split()
        otype = 'close'
        direct = tp[0].upper()
        code = tp[1].upper()
        price = float(tp[2])
        volume = int(tp[3])
        lastoid, doreq, rcok = rc.reqorder(otype, direct, code, price, volume)
        print 'requested,' if doreq else 'unrequested,', 'riskcheck ok,' if (doreq and rcok) else 'riskcheck failed,', lastoid
        self.lastoid = lastoid

    def do_cancel(self, args):
        pass

def main():
    mysec = 'rcstrat'

    lastoid = None
    while 1:
        try:
            m = raw_input('%d New order or cancle? ' % pid)
            tp = m.split()
            if m.startswith('cancel'):
                try:
                    rc.cancelorder(tp[1])
                except IndexError:
                    rc.cancelorder(lastoid)
            elif m.startswith('open') or m.startswith('close'):
                otype = tp[0].upper()
                direct = tp[1].upper()
                code = tp[2].upper()
                price = float(tp[3])
                volume = int(tp[4])
                lastoid, doreq, rcok = rc.reqorder(otype, direct, code, price, volume)
                print 'requested,' if doreq else 'unrequested,', 'riskcheck ok,' if (doreq and rcok) else 'riskcheck failed,', lastoid
            elif m.startswith('pos'):
                tbook.printpos()
            elif m.startswith('order'):
                try:
                    tbook.printorder(tp[1])
                except IndexError:
                    tbook.printorder(lastoid)
            elif m.startswith('alloid'):
                tbook.printalloid()
            else:
                print 'Unkown command.'

        except KeyboardInterrupt:
            print 'now exit'
            break

    rc.stop()
    rcbottom.stop()
    tbproxy.stop()

if __name__=='__main__':
    main()
    sys.exit(1)
# $Id$ 
