import sys
import time

from flamelib import Engine, getstore, getpubsub
import config

if __name__=='__main__':

    mysec = 'engine'
    cfg = config.parseconfig()
    mycfg = cfg[mysec]
    storecfg = cfg[mycfg['store']]
    storecfg['port'] = int(storecfg['port'])
    storecfg['db'] = int(storecfg['db'])
    ans = raw_input('Using ctp config: %s, sure? ' % mycfg['trader'])
    if not ans.startswith('y'):
        sys.exit(1)
    tradercfg = cfg[mycfg['trader']]

    config.setuplogger(mysec)

    store = getstore(storecfg)
    pubsub = getpubsub(storecfg)

    if store is None or pubsub is None:
        raise Exception('connect to store or pubsub failed.')

    engine = Engine(tradercfg, pubsub)
    engine.start()

    print 'Engine start.'
    while 1:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            try:
                ret = raw_input('Stop engine? ')
                if ret[0] == 'y':
                    break
            except KeyboardInterrupt:
                print 'Continue'

    engine.stop()
    engine.join()
    print 'Engine quit.'


# $Id$ 
