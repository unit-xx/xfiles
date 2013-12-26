# a risk-checking strategy, which also test engine.

from flamelib import strattop, stratbottom, getstore, getpubsub
import flaredef as fdef
import config

class rcstrat(strattop):
    def setup(self):
        chresp = fdef.fullname(fdef.CHORESP, self.strat)
        self.pubsub.subscribe((chresp, fdef.CHQUOTE))

    def riskcheck(self):
        pass

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

    lastoid = None
    dirct = fdef.VSHORT
    code = 'IF1401'
    while 1:
        try:
            m = raw_input('An order or cancle? ')
            if m.startswith('cancel'):
                s
            elif m.startswith('open'):
                s
            elif m.startswith('close'):
                s

        except KeyboardInterrupt:
            break

if __name__=='__main__':
    main()
