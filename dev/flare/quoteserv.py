import time

from flamelib import qrepo, getstore, getpubsub
import config

if __name__=='__main__':

    mysec = 'quoteserver'
    cfg = config.parseconfig()
    mycfg = cfg[mysec]
    storecfg = cfg[mycfg['store']]
    storecfg['port'] = int(storecfg['port'])
    storecfg['db'] = int(storecfg['db'])
    mdcfg = cfg[mycfg['mdaccount']]

    config.setuplogger(mysec)

    store = getstore(storecfg)
    pubsub = getpubsub(storecfg)

    qserv = qrepo(['IF1401', 'IF1402'], mdcfg, pubsub, store)
    qserv.setup()

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

    qserv.stop()

# $Id$ 
