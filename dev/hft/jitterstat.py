# get stats for sif jitters within certain ticks, for a day.

import sys, gzip, os
import math
import util

# usage: quotefile tickcount sifindex
qfn = sys.argv[1]
ntick = int(sys.argv[2])
sifindex = 0
try:
    sifindex = sys.argv[3]
except IndexError:
    pass

if qfn.endswith(".gz"):
    qf = gzip.open(qfn)
else:
    qf = open(qfn)

sifs = util.calsicontracts(os.path.basename(qfn).split(".")[0][3:])
sif = sifs[sifindex]
lastnq = []
avg = 0.0
var = 0.0
sqravg = 0.0
stddev = 0.0
baspread = 0.0
count = 0

zcrossmax = ntick - 1
zcrossper = 0.0
zcross = 0

schema = "date, time, index, avg, stdev, max-min, spread, z-cross, z-cross%"
print "#", schema
for line in qf:
    tmp = line.split()
    if len(tmp) != 12:
        continue

    if sif == tmp[4]:
        lastq = float(tmp[5])
        lastnq.append(lastq)

        avg = avg + lastq/ntick
        sqravg = sqravg + lastq*lastq/ntick
        baspread = float(tmp[10]) - float(tmp[8])
        if len(lastnq) > ntick:
            count = count + 1
            firstq = lastnq[0]
            avg = avg - firstq/ntick
            sqravg = sqravg - firstq*firstq/ntick
            var = sqravg - avg*avg
            del lastnq[0]
            try:
                stddev = math.sqrt(var)
            except ValueError:
                #var is too small and it's considered as negative float
                stddev = 0.0

            zcross = util.getcross(lastnq, avg)
            zcrossper = float(zcross) / zcrossmax

            print tmp[0], tmp[2], count, "%.1f"%avg, "%.2f"%stddev, "%.1f"%(max(lastnq)-min(lastnq)), "%.1f"%baspread, zcross, "%.2f"%zcrossper
