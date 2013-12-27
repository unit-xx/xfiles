# a risk-checking strategy, which also test engine.

import os, sys

from flamelib import strattop, stratbottom, getstore, getpubsub
import flaredef as fdef
import config
from util import Record

class rcstrat(strattop):
    def setup(self):
        chresp = fdef.fullname(fdef.CHORESP, self.strat)
        self.pubsub.subscribe((chresp, fdef.CHQUOTE))

    def riskcheck(self):
        pass

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

    config.setuplogger(mysec)

    store = getstore(storecfg)
    pubsub = getpubsub(storecfg)

    rc = rcstrat(mysec, pubsub, None)
    rcbottom = stratbottom(pubsub, rc)

    rcbottom.start()
    rc.start()

    print os.getpid()

    lastoid = None
    dirct = fdef.VSHORT
    code = 'IF1401'
    while 1:
        try:
            m = raw_input('An order or cancle? ')
            tp = m.split()
            if m.startswith('cancel'):
                print 'Not impl.'
            elif m.startswith('open'):
                o = neworder(fdef.VOPEN, tp[1].upper(), tp[2].upper(), float(tp[3]), int(tp[4]))
                rc.reqorder(o)
            elif m.startswith('close'):
                o = neworder(fdef.VCLOSE, tp[1].upper(), tp[2].upper(), float(tp[3]), int(tp[4]))
                rc.reqorder(o)

        except KeyboardInterrupt:
            break

if __name__=='__main__':
    main()
    sys.exit(1)
