# config mm params, listens for quotes etc., and generate signals
# manage ptf and orders
# link strat with tbook
# setup all components and run
# monitor and risk measures.

class mmpair(strattop):
    def __init__(self, pubsub, tbook):
        strattop.__init__(self)
        self.pubsub = pubsub
        self.tbook = tbook

    def setup(self):
        pass

    def signal(self):
        pass

