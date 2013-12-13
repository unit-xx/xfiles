# config mm params, listens for quotes etc., and generate signals
# manage ptf and orders
# link strat with tbook
# setup all components and run
# external: engine, quote, MAcalc, redis
# internal: TBookCache, TBookProxy
# monitor and risk measures.
# define namespace prefix.
# config params.

import config
import flaredef as fdef

class mmpair(strattop):
    def __init__(self, pubsub, tbook):
        strattop.__init__(self)
        self.pubsub = pubsub
        self.tbook = tbook
        self.config = config.gconfig

        self.qchannel = x
        self.machannel = x

        self.ptf = x
        self.tradeparam = x

    def setup(self):
        self.pubsub.subscribe(x)
        # load ptfdef
        # new ptf instance
        # init and check tbook
        # define name schema

        # TODO: define tbook and checks link with strat
        # TODO: name schema
        # TODO: engine, mmbottom
        # TODO: need to reserve? and how?

        # other param/variable initialization.

    def signal(self):
        msg = self.pubsub.listen()
        if msg = xxx:
            # acquire new ptf instance
            # check risk condition
            # submit order
            # update tbook
            if action == openclose:
                # TODO: self.risk.check()
                self.reqorder()
            elif action == cancel:
                self.cancelorder()

    def reqorder(self, o):
        '''
        o is a order of type Record

        order keys defined in flaredef:

        oid, strat, ptfid, 
        code, longshort, openclose, price, volume,

        sequence is important: publish first, or booking first?
        Rules: 1) orders who cut margin from cash need booking first
        2) orders who free margin to cash need orders first.

        '''
        o[fdef.KACTION] = fdef.VINSERT
        self.pubsub.publish(fdef.CHOREQ, o)
        o[fdef.KOSTATE] = fdef.VORDERREQED
        self.tbook.updateorder(o)

    def cancelorder(self):
        o[fdef.KACTION] = fdef.VCANCEL
        self.pubsub.publish(fdef.CHOREQ, o)
        o[fdef.KOSTATE] = fdef.VORDERREQED
        self.tbook.updateorder(o)


class mmpairbtm(stratbottom):
    pass

def main():
    cfg = config.parseconfig()
    config.init_gconfig(cfg)

    # logger, config, ...
    # components setup and connection.
    # risk measure

