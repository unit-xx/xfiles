import cPickle as pickle
from prettytable import PrettyTable

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

def printdictdict(d, rowkey, colkey):
    ck = [x for x in colkey]
    ck.insert(0, 'ROWKEY')
    tbl = PrettyTable(ck)
    tbl.padding_width = 1
    for rk in rowkey:
        row = [d[rk][x] for x in colkey]
        row.insert(0, rk)
        tbl.add_row(row)
    print tbl


