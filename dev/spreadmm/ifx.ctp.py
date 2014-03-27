# this is the counterpart of ifx.py, and it deals with CTP quotation 
# records which is saved one file per day

# PURPOSE: read a ctp quote records file (e.g. quote.20140214.csv) and 
# write quotes of if1/2/3/4 to separate files.

import sys, csv, os
import util
from datetime import date
from operator import itemgetter

qfn = sys.argv[1]
ifN = 4 # 4 contracts at a time

qf = open(qfn)
rd = csv.reader(qf)
r = rd.next() # skip header
colnum = len(r)

# print header line
header = ['tradeday', 'tradetime', 'update_id', 'contract_time', 'buyprice1', 'buyvolume1', 'sellprice1', 'sellvolume1']

ifcal = util.IFCalendar()

# 1. pick out ifn
tday = None
bbuf = [[] for i in range(ifN)]

for r in rd:
    if len(r)!=colnum:
        continue

    if not r[3].startswith('IF'):
        continue

    if r[0] != tday:
        tday = r[0]
        d = date(int(tday[0:4]), int(tday[4:6]), int(tday[6:8]))
        ifall = ifcal.clist(d,2)

    try:
        ifnum = ifall.index(r[3])
    except ValueError:
        continue

    rec = [
            r[0],
            '%s.%03d'%(r[1],int(r[2])),
            -1,
            r[3][2:],
            r[12],
            r[13],
            r[14],
            r[15]
            ]
    bbuf[ifnum].append(rec)

# print buf
for i in range(ifN):
    ofn = '%s.if%d' % (os.path.basename(qfn).split('.')[1], i+1)
    wrt = csv.writer(open(ofn, 'wb'), delimiter=' ')
    wrt.writerow(header)
    for r in bbuf[i]:
        wrt.writerow(r)

