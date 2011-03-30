#spread for a day
import sys, os

from datetime import date

import util

datafn = sys.argv[1]
datafnb = os.path.basename(sys.argv[1])#siqYYYYMMDD.log
dataday = date(int(datafnb[3:7]), int(datafnb[7:9]), int(datafnb[9:11]))

si = util.calsicontracts(dataday)
si1 = si[0]
si2 = si[1]
q1 = 0.0
q2 = 0.2
lasttick = None

data = open(datafn)
for line in data:
    tmp = line.split()
    if len(tmp) != 12:
        continue

    tick = tmp[2]
    if tick != lasttick:
        if lasttick is not None:
            print lasttick, "%.1f"%(q2-q1)
        lasttick = tick
    else:
        if si1 == tmp[4]:
            q1 = float(tmp[5])
        elif si2 == tmp[4]:
            q2 = float(tmp[5])

