# CalendaR ARbitrage.

import sys
import cPickle as pickle

from flamelib import stratconsole, runstrat, strattop
import flaredef as fdef
import config

class crabstrat(strattop):
    def setup(self):
        self.mycfg['maxvolperorder'] = int(self.mycfg['maxvolperorder'])
        self.chma = self.mycfg['machannel']

        self.pubsub.subscribe((fdef.CHQUOTE, self.chma, fdef.CHHEARTBEAT))
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

    def signal(self, m):
        #print >>sys.stderr, m['channel']
        ma = defaultdict(dict)
        madiff = 0.0

        
        if m['channel'] == fdef.CHQUOTE:
            q = pickle.loads(m['data'])
            # q = dict()
            print q
        elif m['channel'] == self.chma:
            q = pickle.loads(m['data'])
            # q = (inst, tu, maval)

class crabconsole(stratconsole):
    pass

def main():
    mysec = 'crabstrat'
    runstrat(mysec, crabstrat, crabconsole)

if __name__=='__main__':
    main()

# $Id$
