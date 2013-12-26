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
    tradercfg = cfg[mycfg['trader']]

    config.setuplogger(mysec)

    store = getstore(storecfg)
    pubsub = getpubsub(storecfg)

    engine = Engine(tradercfg, pubsub)
    engine.start()

    print 'Engine start.'
    while 1:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            try:
                ret = raw_input('Stop quote server? ')
                if ret[0] == 'y':
                    break
            except KeyboardInterrupt:
                print 'Continue'

    engine.stop()
    engine.join()
    print 'Engine quit.'


