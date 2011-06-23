# calcuate volumn-weighted average price

import sys
import time
import datetime
import socket
import zlib
import pickle
import math
from struct import unpack

TARGET = "1105"
MODE = "V"#V for volumn weighted average.

pv = [] # price, volume, p*v
lastdv = 0

maxqlen = [int(x) for x in sys.argv[2:]]
maxqlen.sort(reverse=True)
volsum = [0 for x in maxqlen]
weightpsum = [0.0 for x in maxqlen]
awp = [0.0 for x in maxqlen]
avol = [0 for x in maxqlen]

weightp2sum = [0.0 for x in maxqlen]
wstdev = [0.0 for x in maxqlen]

f = open(sys.argv[1])

"""
1. read a quote to setup lastdv
2. accumulate until enough quotes
3. update by minus oldest quote and add latest quote
"""

oktowhile = True
while oktowhile:
    qd = f.readline().split()
    if len(qd) != 12:
        continue
    if qd[3] == "IF" and qd[4] == TARGET:
        lastdv = int(qd[6])
        oktowhile = False
        break

oktowhile = True
while oktowhile:
    qd = f.readline().split()
    if len(qd) != 12:
        continue
    if qd[3] == "IF" and qd[4] == TARGET:
        if MODE == "V":
            v = int(qd[6]) - lastdv
        else:
            v = 1
        p = float(qd[5])
        pv.append((p, v, p*v))
        lastdv = int(qd[6])

        if len(pv) == maxqlen[0]:# the largest length
            for i, qlen in enumerate(maxqlen):
                volsum[i] = sum([x[1] for x in pv[-qlen:]])
                weightpsum[i] = sum([x[2] for x in pv[-qlen:]])
                weightp2sum[i] = sum([x[2]*x[0] for x in pv[-qlen:]])
            oktowhile = False
            break
#print pv
#print volsum, weightpsum

#print "schema"
print "#date, time, price, price-delta*%d, awp*%d, stdev*%d, avol*%d" % ((len(awp),)*4)
while 1:
    qd = f.readline().split()
    if len(qd) == 0:
        break
    if len(qd) != 12:
        continue
    if qd[3] == "IF" and qd[4] == TARGET:
        if MODE == "V":
            v = int(qd[6]) - lastdv
        else:
            v = 1
        p = float(qd[5])
        lastdv = int(qd[6])

        for i, qlen in enumerate(maxqlen):
            volsum[i] = volsum[i] + v - pv[-qlen][1]
            #print "vol add %d, minus %d" % (v, pv[-qlen][1])
            weightpsum[i] = weightpsum[i] + p*v - pv[-qlen][2]
            weightp2sum[i] = weightp2sum[i] + p*p*v - pv[-qlen][2]*pv[-qlen][0]
            #print "weightpsum add %.2f, minus %.2f" % (p*v, pv[-qlen][2])
            #print volsum, weightpsum

            avol[i] = volsum[i]/qlen
            try:
                awp[i] = weightpsum[i]/volsum[i]
            except ZeroDivisionError:
                awp[i] = float(qd[5])

            try:

                wstdev[i] = math.sqrt(weightp2sum[i]/volsum[i] - awp[i]*awp[i])
            except ValueError:
                wstdev[i] = 0.0
            except ZeroDivisionError:
                wstdev[i] = 0.0

            if len(pv) > 30*maxqlen[0]:
                del pv[0:-maxqlen[0]]

        pv.append((p, v, p*v))
        #print "#date, time, price, price-delta*%d, awp*%d, stdev*%d, avol*%d" % (len(awp))*4
        print qd[0], qd[1], "%.1f"%p, " ".join(["%.1f"%(p-x) for x in awp]), " ".join(["%.1f"%x for x in awp]), " ".join(["%.1f"%x for x in wstdev]), " ".join(["%d"%x for x in avol])
