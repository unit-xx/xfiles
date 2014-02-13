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

        self.machannel = mycfg['machannel']
        self.secperunit = int(mycfg['secperunit'])
        self.mawsize = int(mycfg['mawsize'])

        # code -> buffer unit
        self.unitlen = defaultdict(dict)
        self.unitsum = defaultdict(dict)
        # code -> current buffer tick unit
        self.curunit = {}

        self.runflag = True
        self.logger = logging.getLogger()
        self.name = self.__class__.__name__

    def setup(self):
        self.pubsub.subscribe((fdef.CHQUOTE, fdef.CHHEARTBEAT))
        return True

    def qma(self, q):
        '''
        Calculate ma (moving average) as follows.

        Organize quote into time unit, whose length is defined by secperunit.
        Tick numbers and sum of mid-price is maintained in unitlen and unitsum.
        When the latest tick move into a new unit, generate MA value for the
        last time unit.
        '''
        inst = q['code']
        tu = int(q['tic'] / self.secperunit)
        midprice = 0.0
        midlen = 0

        if q['bid1']>q['upperlimit'] or q['bid1']<q['lowerlimit'] or q['ask1']>q['upperlimit'] or q['ask1']<q['lowerlimit']:
            midprice = 0.0
            midlen = 0
        else:
            midprice = (q['bid1'] + q['ask1'])/2
            midlen = 1

        try:
            cunit = self.curunit[inst]
        except KeyError:
            self.curunit[inst] = tu
            self.unitsum[inst][tu] = midprice
            self.unitlen[inst][tu] = midlen
            return

        if tu != cunit:
            # step into new time unit, calc and publish MA for latest time unit
            ttsum = 0.0
            ttlen = 0.0
            maval = None
            zerounit = 0
            starttick = cunit
            hitunit = 0

            if len(self.unitsum[inst])<self.mawsize:
                print 'not enough data %s, tick %d' % (inst, tu)
            else:
                while 1:
                    try:
                        ttsum += self.unitsum[inst][starttick]
                        ttlen += self.unitlen[inst][starttick]
                        if self.unitlen[inst][starttick]==0:
                            zerounit += 1
                        hitunit += 1
                    except KeyError:
                        pass

                    starttick -= 1
                    if hitunit >= self.mawsize:
                        break

                    if starttick < 0:
                        print 'loop error %s, tick %d' % (q['code'], tu)
                        break

                if hitunit >= self.mawsize:
                    if float(zerounit)/self.mawsize > 0.1:
                        print 'too many zero unit %s, tick %d' % (q['code'], tu)
                    else:
                        try:
                            maval = ttsum/ttlen
                        except ZeroDivisionError:
                            print 'divide by zero %s, tick %d' % (q['code'], tu)

                        if maval is not None:
                            try:
                                mad = pickle.dumps((inst, cunit, maval))
                                self.pubsub.publish(self.machannel, mad)
                                print 'new ma %s' % str((inst, cunit, maval))
                            except:
                                self.logger.exception('dump ma value.')

            self.curunit[inst] = tu
            self.unitsum[inst][tu] = midprice
            self.unitlen[inst][tu] = midlen
        else:
            self.unitsum[inst][tu] += midprice
            self.unitlen[inst][tu] += midlen

        return

    def run(self):
        if not self.setup():
            self.logger.warning('What\'s wrong!')

        while self.runflag:
            m = self.pubsub.listen()
            if m['channel'] == fdef.CHHEARTBEAT:
                continue

            try:
                q = pickle.loads(m['data'])
                self.qma(q)
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
    secperunit = int(mycfg['secperunit'])
    mawsize = int(mycfg['mawsize'])
    console.cmdloop('running MA server with secperunit %d, mawsize %d, type `help\' for commands' % (secperunit, mawsize))

    ms.stop()
    signal.signal(signal.SIGINT, oldhandler)
    runlock(store, mysec)

if __name__=='__main__':
    main()

# $Id$
