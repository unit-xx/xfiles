# a set of test cases required by risk management department.

import os, sys, time

from flamelib import stratconsole, runstrat, strattop
import flaredef as fdef
import config

class testtop(strattop):
    def setup(self):
        self.maxvolperorder = int(self.mycfg['maxvolperorder'])
        self.pubsub.subscribe((fdef.CHQUOTE, fdef.CHHEARTBEAT))

        print 'maxvolperorder = %d' % self.maxvolperorder
        print 'position limitations'
        print self.tbook.posmax
        print

        return True

    def riskcheck(self, oid):
        o, olk = self.tbook.getorder(oid)
        ret = False
        if o is not None:
            with olk:
                vol = o[fdef.KVOLUME]
                if self.maxvolperorder < 0 or vol <= self.maxvolperorder:
                    ret = True
                else:
                    ret = False
        #self.logger.debug('order %s rc result: %s', oid, ret)
        return ret

    def onOrderRejected(self, oid, resp):
        oid = resp[fdef.KOID]
        print '%s is rejected (%s)' % (oid, resp)

    def onOrderAccepted(self, oid, resp):
        oid = resp[fdef.KOID]
        print '%s is accepted (%s)' % (oid, resp)

class testconsole(stratconsole):
    def do_test(self, args):
        tp = args.split()
        try:
            longcode = tp[0]
            longvol = int(tp[1])
            shortcode = tp[2]
            shortvol = int(tp[3])
            price = float(tp[4])
            interval = float(tp[5])
            print longcode, longvol, shortcode, shortvol, price, interval
        except (IndexError, ValueError):
            print 'argument error: longcode longvol shortcode shortvol price interval'
            return

        try:
            while 1:
                shortoid, doreq, rcok = self.top.reqorder(fdef.VOPEN, fdef.VSHORT, shortcode, price-50, shortvol)
                print 'Short %d requested (%s, %s, %s)' % (shortvol, shortoid, doreq, rcok)

                longoid, doreq, rcok = self.top.reqorder(fdef.VOPEN, fdef.VLONG, longcode, price+50, longvol)
                print 'Long %d requested (%s, %s, %s)' % (longvol, longoid, doreq, rcok)


                time.sleep(interval)
        except (KeyboardInterrupt, IOError):
            print 'exit loop'

def main():
    mysec = sys.argv[1]
    runstrat(mysec, testtop, testconsole)

if __name__=='__main__':
    main()
    sys.exit(1)

# $Id$

