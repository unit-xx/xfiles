from threading import Thread

class strattop(Thread):
    '''
    1. a defined strategy task has only one instance at any time.
    2. when a strategy task is restarted, it has to recover from previous run, including orders, positions, margins, cash account, etc.
    3. 
    '''
    def __init__(self):
        Thread.__init__(self)
        self.runflag = True
        self.name = self.__class__.__name__

class mmpair(strattop):
    def __init__(self, pubsub, tbook):
        strattop.__init__(self)
        self.pubsub = pubsub
        self.tbook = tbook

p = mmpair('a', 'b')
