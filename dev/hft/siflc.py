# linear combination of stock index futures

import sys, os
import util
import datetime

sifindex = [0,1]
#sifweight = [-3,4,-1]#for 569
#sifweight = [-2,3,-1]#for 679
sifweight = [-1,1]#for 67
sifpricebuy = [0.0]*len(sifindex)#price to use when buy the portfolio
sifpricesell = [0.0]*len(sifindex)
siflcbuy = 0.0
siflcsell = 0.0

qfn = sys.argv[1]
sifs = util.calsicontracts(os.path.basename(qfn).split(".")[0][3:])
#thedate = datetime
mktopentime = datetime.time(9, 15, 00)
mktclosetime = datetime.time(15, 15, 00)

sifupdate = [0] * len(sifindex)
skipcount = 0
skipmax = 10

for line in open(qfn):
    tmp = line.split()
    qt = datetime.datetime.strptime(tmp[2], "%H:%M:%S").time()
    if qt >= mktclosetime or qt <= mktopentime:
        continue

    i = sifs.index(tmp[4])
    if i in sifindex:
        pb = float(tmp[-4])
        pa = float(tmp[-2])

        if sifweight[i] < 0:
            sifpricebuy[i] = pb
            sifpricesell[i] = pa
        else:
            sifpricebuy[i] = pa
            sifpricesell[i] = pb
        sifupdate[i] = 1

        if sum(sifupdate) == len(sifupdate):
            skipcount = skipcount + 1

            if skipcount >= skipmax:
                skipcount = 0
                sifupdate = [0]*len(sifindex)
                siflcbuy = sum([sifweight[i]*sifpricebuy[i] for i in range(len(sifindex))])
                siflcsell = sum([sifweight[i]*sifpricesell[i] for i in range(len(sifindex))])
                print tmp[0], tmp[1], "%.1f"%siflcbuy, "%.1f"%siflcsell, "%.1f"%(siflcbuy-siflcsell)


