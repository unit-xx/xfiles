import time
import sys
import logging
import signal
from collections import defaultdict
import cPickle as pickle
from threading import Thread
from cmd import Cmd

from flamelib import getpubsub, getstore, rlock, runlock
import flaredef as fdef
import config

class maserv(Thread):
    def __init__(self, pubsub, mycfg):
        Thread.__init__(self)

        self.mycfg = mycfg
        self.pubsub = pubsub

        # code -> lastest MA, using mid-price
        self.ma = {}
        # code -> buffer unit
        self.buflen = defaultdict(list)
        self.bufsum = defaultdict(list)
        # code -> current buffer tick unit
        self.curbuf = {}
        self.lastvol = 0

        self.runflag = True
        self.logger = logging.getLogger()
        self.name = self.__class__.__name__

    def setup(self):
        self.pubsub.subscribe((fdef.CHQUOTE, fdef.CHHEARTBEAT))
        return True

    def qma(self, q):
        inst = q['code']

        if len(self.buflen[inst])==0:
            self.buflen[inst].append(0.0)
            self.bufsum[inst].append(0.0)


    def run(self):
        if not self.setup():
            self.logger.warning('What\'s wrong!')

        while self.runflag:
            m = self.pubsub.listen()
            if m['channel'] == fdef.CHHEARTBEAT:
                continue

            try:
                quote = pickle.loads(m['data'])
                if q is None:
                    return

                if q.BidPrice1 > q.UpperLimitPrice or q.BidPrice1 < q.LowerLimitPrice:
                    return

                if q.AskPrice1 > q.UpperLimitPrice or q.AskPrice1 < q.LowerLimitPrice:
                    return

                self.qma(quote)
            except:
                self.logger.exception('Wrong data.')
        self.logger.info('Quit ma server.')

    def stop(self):
        self.runflag = False
        self.pubsub.publish(fdef.CHHEARTBEAT, 'hello')

class emptyconsole(Cmd):
    def do_quit(self, args):
        """Quits the program."""
        print "Quitting."
        return True

    def do_EOF(self,line):
        print 'type `quit\' to exit.'
    
def main():
    mysec = 'maserv'

    cfg = config.parseconfig()
    mycfg = cfg[mysec]

    storecfg = cfg[mycfg['store']]
    storecfg['port'] = int(storecfg['port'])
    storecfg['db'] = int(storecfg['db'])

    config.setuplogger(mysec)

    store = getstore(storecfg)
    pubsub = getpubsub(storecfg)
    if store is None or pubsub is None:
        logging.error('Cannot get pubsub')
        sys.exit(1)

    if not rlock(store, mysec):
        print 'Another instance is running, I quit.'
        sys.exit(1)

    ms = maserv(pubsub, mycfg)
    ms.start()

    oldhandler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    console = emptyconsole()
    console.prompt = '> '
    console.cmdloop('running MA server, type `help\' for commands')

    ms.stop()
    signal.signal(signal.SIGINT, oldhandler)
    runlock(store, mysec)

if __name__=='__main__':
    main()

# $Id$
