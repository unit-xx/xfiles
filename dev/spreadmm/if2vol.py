# read through a quotation stream, figure out if2 contracts, output vol and others.
# NOTE: quotation chron order not checked.
# assumption: quotation is ordered by date/update_id

import sys, csv
import util
from datetime import date
from operator import itemgetter

f = open(sys.argv[1])
rd = csv.reader(f)
r = rd.next() # skip header
oindex = [0,1,3,6,24,25,26,27]
for i in oindex:
    print r[i].lower(),
print

ifcal = util.IFCalendar()
tday = None
if2 = ""
ttime = None
tcnt = 1
buf = []
for r in rd:
    if r[0] != tday:
        tday = r[0]
        d = date(int(tday[0:4]), int(tday[4:6]), int(tday[6:8]))
        if2 = ifcal.clist(d,1)[1]

    if r[6] == if2:
        if r[1] != ttime:
            buf.sort(key=itemgetter(3))
            step = 1000/tcnt
            for j, b in enumerate(buf):
                b[1] = '%s.%03d' % (b[1], j*step)
                for i in oindex:
                    print b[i],
                print
            tcnt = 0
            buf = []

        tcnt += 1
        ttime = r[1]
        buf.append(r)


