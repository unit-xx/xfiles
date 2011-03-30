# how many cuts a stock in HS300 arbitrage portfolio can be splitted.

import sys
import pickle
from dbfpy import dbf

dbsh = dbf.Dbf("z:\\show2003.dbf", ignoreErrors=True, readOnly=True)
dbsz = dbf.Dbf("z:\\sjshq.dbf", ignoreErrors=True, readOnly=True)
shmap = pickle.load(open('shmap.pkl'))
szmap = pickle.load(open('szmap.pkl'))

sxf = 0.0003
sxfmin = 5.00

shghf = 0.001
szghf = 0.0
ghfmin = 1.00

ptf = open(sys.argv[1])

for line in ptf:
    if line == "":
        break

    tp = line.split(",")
    if tp[0] == 'SZ':
        code = tp[1]
        count = int(tp[2])
        price = dbsz[szmap['SZ'+code]]["HQZJCJ"]
        cost = count * price
        maxcut = max(int(cost*sxf/sxfmin), 1)
        print 'SZ', code, count, price, cost, maxcut
    elif tp[0] == 'SH':
        code = tp[1]
        count = int(tp[2])
        price = dbsh[shmap['SH'+code]]["S8"]
        cost = count * price
        maxcut = max(int(min(cost*sxf/sxfmin, count*shghf/ghfmin)), 1)
        print 'SH', code, count, price, cost, maxcut
