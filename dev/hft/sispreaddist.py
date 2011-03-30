#spread distribution for multi-days. Currently avg, stdev, min, max.
# One day per line.

import sys, os, glob, math

from datetime import date

import util

datadir = sys.argv[1]
datafns = glob.glob(os.path.join(datadir, "siq*.log"))
datafns.sort()


print "# logfn, index, average, stdev, minq, maxq"
for datafn in datafns:
    datafnb = os.path.basename(datafn)#siqYYYYMMDD.log
    dataday = date(int(datafnb[3:7]), int(datafnb[7:9]), int(datafnb[9:11]))
    si = util.calsicontracts(dataday)
    si1 = si[0]
    si2 = si[1]

    q1 = 0.0
    q2 = 0.0
    lasttick = None

    minq = float('Inf')
    maxq = float('-Inf')
    totalcnt = 0
    totalsum = 0.0
    totalsumsqr = 0.0
    avgq = 0.0
    stdev = 0.0

    data = open(datafn)
    for line in data:
        tmp = line.split()
        if len(tmp) != 12:
            continue

        tick = tmp[2]

        if tick != lasttick:
            if lasttick is not None:
                if q1 != 0.0 and q2 != 0.0:
                    totalcnt = totalcnt + 1
                    spread = q2 - q1
                    totalsum = totalsum + spread
                    totalsumsqr = totalsumsqr + spread*spread
                    minq = min(minq, spread)
                    maxq = max(maxq, spread)
            lasttick = tick
        else:
            if si1 == tmp[4]:
                q1 = float(tmp[5])
            elif si2 == tmp[4]:
                q2 = float(tmp[5])
    avgq = totalsum / totalcnt
    stdev = math.sqrt(totalsumsqr/totalcnt - avgq*avgq)
    print os.path.basename(datafn), datafns.index(datafn)+1, "%.1f"%avgq, "%.1f"%stdev, minq, maxq
