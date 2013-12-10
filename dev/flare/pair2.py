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

        # other param/variable initialization.


    def signal(self):
        msg = self.pubsub.listen()
        if msg = xxx:
            # acquire new ptf instance
            # check risk condition
            # submit order
            # update tbook
            pass

class mmpairbtm(stratbottom):
    pass

def main():
    cfg = config.parseconfig()
    config.init_gconfig(cfg)

    # logger, config, ...
    # components setup and connection.
    # risk measure

