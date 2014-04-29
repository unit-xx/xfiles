import sys

from flamelib import getstore

import flaredef as fdef
import config

def main():
    cfg = config.parseconfig('initstrat.ini')

    storecfg = {}
    storecfg['host'] = '127.0.0.1'
    storecfg['port'] = 6379
    storecfg['db'] = 1

    store = getstore(storecfg)
    if store is None:
        raise flameException('connect to store failed.')

    if sys.argv[1] == 'ALL':
        initsec = cfg.keys()
    else:
        initsec = sys.argv[1:]

    for sec in initsec:
        seccfg = cfg[sec]
        for k in seccfg:
            print k, seccfg[k]
            if k=='tb':
                store.hset(fdef.TB2STRATMAP, seccfg[k], sec)
            else:
                store.hset(fdef.fullname(fdef.POSMAXNS, sec), k, seccfg[k])

if __name__=='__main__':
    main()
