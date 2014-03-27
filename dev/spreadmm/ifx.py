# from raw quotation files: 
# 1. pick out if1, or(2/3/4)
# 2. order quotation in date/update_id
# 3. add fake milliseconds (quotations usually updated 2 times a seconds, but with same date/time timestamp, differ only in update_id)

import sys, csv
import util
from datetime import date
from operator import itemgetter

qfn = sys.argv[1]
ifn = int(sys.argv[2])-1 # ifn=0 for if1, 1 for if2, etc.

qf = open(qfn)
rd = csv.reader(qf)
r = rd.next() # skip header
oindex = [0,1,3,6,24,25,26,27]

# print header line
for i in oindex:
    print r[i].lower(),
print

ifcal = util.IFCalendar()

# 1. pick out ifn
tday = None
if2 = ""
buf = []
for r in rd:
    if r[0] != tday:
        tday = r[0]
        d = date(int(tday[0:4]), int(tday[4:6]), int(tday[6:8]))
        ifc = ifcal.clist(d,1)[ifn]

    if r[6] == ifc:
        r[3] = int(r[3])
        buf.append(r)

# 2. order in date/update_id
buf.sort(key=itemgetter(0,3))

# 3. add fake milliseconds
# REALLY NEED?
# a. add fake milliseconds to quotations.
# b. milliseconds not necessary, use merge sort tricks to compute spread.
# use solution a, Assumption: every second has 0/1/2 updates, no other options, warning on exceptions.

buf.append('EOF') # a trick to deal with last time stamp issue
ts = ''
sbuf = []
for r in buf:
    if r[1]!=ts:
        scnt = len(sbuf)
        if scnt not in (0,1,2):
            print >>sys.stderr, "Warning: quotatino in time %s has %d updates." % (ts, scnt)

        try:
            step = 1000/scnt
        except ZeroDivisionError:
            pass

        for i, b in enumerate(sbuf):
            b[1] = '%s.%03d' % (b[1], i*step)

        ts = r[1]
        sbuf=[]

    sbuf.append(r)
del buf[-1]

# print buf
for r in buf:
    for i in oindex:
        print r[i],
    print


