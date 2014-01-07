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
    def load(s):
        return pickle.loads(s)

    def __str__(self):
        return u', '.join( u': '.join((unicode(k),unicode(self[k]))) for k in self )

def printdictdict(d, rowkey, colkey):
    ck = [x for x in colkey]
    ck.insert(0, 'ROWKEY')
    tbl = PrettyTable(ck)
    tbl.padding_width = 0
    for rk in rowkey:
        row = [d[rk][x] for x in colkey]
        row.insert(0, rk)
        tbl.add_row(row)
    print tbl


