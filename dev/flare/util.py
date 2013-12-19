import cPickle as pickle

class Record(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

    def __getstate__(self):
        return self

    def __setstate__(self, state):
        self = state

    def dump(self):
        return pickle.dumps(self, -1)

    @staticmethod
    def load(str):
        return pickle.loads(str)


