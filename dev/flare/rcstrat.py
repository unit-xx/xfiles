# a risk-checking strategy, which also test engine.

import os, sys

from flamelib import strattop, stratbottom, getstore, getpubsub, TBookCache, TBookLib, TBookProxy
import flaredef as fdef
import config
from util import Record

class rcstrat(strattop):
    def setup(self):
        chresp = fdef.fullname(fdef.CHORESP, self.strat)
        self.pubsub.subscribe((chresp, fdef.CHQUOTE))

    def riskcheck(self, oid):
        o, olk = self.tbook.getorder(oid)
        ret = False
        if o is not None:
            with olk:
                vol = o[fdef.KVOLUME]
                if vol <= self.rmetric['maxvolperorder']:
                    ret = True
                else:
                    ret = False
        self.logger.debug('order %s rc result: %s', oid, ret)
        return ret

def neworder(otype, direct, code, price, volume):
    o = Record()

    oid = fdef.localoid()

    o[fdef.KOID] = oid
    o[fdef.KSTRAT] = 'rcstrat'
    o[fdef.KISRESERVED] = False
    o[fdef.KOSTATE] = fdef.VORDERINIT
    o[fdef.KCANCELSTATE] = fdef.VCANCELINIT
    
    o[fdef.KACTION] = fdef.VINSERT
    o[fdef.KOTYPE] = otype
    o[fdef.KPRICE] = price
    o[fdef.KCODE] = code
    o[fdef.KDIR] = direct
    o[fdef.KVOLUME] = volume
    return o

def main():
    mysec = 'rcstrat'
    cfg = config.parseconfig()
    mycfg = cfg[mysec]

    storecfg = cfg[mycfg['store']]
    storecfg['port'] = int(storecfg['port'])
    storecfg['db'] = int(storecfg['db'])
    tbname = mycfg['tbname']

    config.setuplogger(mysec)

    store = getstore(storecfg)
    pubsub = getpubsub(storecfg)

    tblib = TBookLib(store, tbname)
    print tblib.setup()
    tbproxy = TBookProxy(pubsub, store, tblib)

    tbook = TBookCache(mysec, tbproxy)
    print tbook.setup()
    rmetric = {}
    rmetric['maxvolperorder'] = int(mycfg['maxvolperorder'])
    rc = rcstrat(mysec, pubsub, tbook, rmetric)
    rcbottom = stratbottom(pubsub, rc)

    rcbottom.start()
    rc.start()

    pid = os.getpid()

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
            break

if __name__=='__main__':
    main()
    sys.exit(1)
