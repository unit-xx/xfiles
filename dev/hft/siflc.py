# linear combination of stock index futures

import sys, os
import util

sifindex = [0,1]
sifweight = [0,1]
sifprice = [0.0]*len(sifindex)
siflc = 0.0

qfn = sys.argv[1]
sifs = util.calsicontracts(os.path.basename(qfn).split(".")[0][3:])

sifupdate = [0] * len(sifindex)
skipcount = 0
skipmax = 10

for line in open(qfn):
    tmp = line.split()
    i = sifs.index(tmp[4])
    if i in sifindex:
        if sum(sifupdate) == len(sifupdate):
            if i == 0:
                skipcount = skipcount + 1
            if skipcount >= skipmax:
                skipcount = 0
                sifupdate = [0]*len(sifindex)
        else:
            p = float(tmp[5])
            if sifupdate[i] == 0:
                sifprice[i] = p
                sifupdate[i] = 1
                if sum(sifupdate) == len(sifupdate):
                    siflc = sum([sifweight[i]*sifprice[i] for i in range(len(sifindex))])
                    print tmp[0], tmp[1], "%.1f"%siflc


