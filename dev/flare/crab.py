# CalendaR ARbitrage.

import sys
import cPickle as pickle

from flamelib import stratconsole, runstrat, strattop
import flaredef as fdef
import config

class crabstrat(strattop):
    def setup(self):
        self.chma = self.mycfg['machannel']
        self.maxvolperorder = int(self.mycfg['maxvolperorder'])

        self.sigma = float(self.mycfg['sigma'])
        self.intensity = float(self.mycfg['intensity'])
        self.qmax = int(self.mycfg['qmax'])
        self.quickleg = self.mycfg['quickleg']
        self.lazyleg = self.mycfg['lazyleg']

        self.sprdmid = 0.0
        self.sprdmidfix = 0.0
        self.qhold = 0

        self.pubsub.subscribe((fdef.CHQUOTE, self.chma, fdef.CHHEARTBEAT))

        return True

    def riskcheck(self, oid):
        o, olk = self.tbook.getorder(oid)
        ret = False
        if o is not None:
            with olk:
                vol = o[fdef.KVOLUME]
                if vol <= self.maxvolperorder:
                    ret = True
                else:
                    ret = False
        self.logger.debug('order %s rc result: %s', oid, ret)
        return ret

    def signal(self, m):
        # using MA value as midprice of spread
        midprice = defaultdict(dict)

        madiff = 0.0

        if m['channel'] == fdef.CHQUOTE:
            try:
                inst, tickunit, maval = pickle.loads(m['data'])
            except:
                pass
            # q = dict()

        elif m['channel'] == self.chma:
            # q = (inst, tu, maval)
            try:
                inst, tickunit, maval = pickle.loads(m['data'])
            except:
                pass

            if inst==self.quickleg or inst==self.lazyleg:
                midprice[inst]['ticku'] = tickunit
                midprice[inst]['value'] = maval
                try:
                    if midprice[self.quickleg]['ticku']==midprice[self.lazyleg]['ticku']:
                        self.sprdmid = midprice[self.lazyleg]['value'] - midprice[self.quickleg]['value']
                        self.sprdmidfix = self.sprdmid - self.qhold * self.sigma
                except KeyError:
                    # no ma has been received
                    pass
                except TypeError:
                    # ma is none since not enough quotes is accumulated to calc ma
                    pass


class crabconsole(stratconsole):
    pass

def main():
    mysec = 'crabstrat'
    runstrat(mysec, crabstrat, crabconsole)

if __name__=='__main__':
    main()

# $Id$
