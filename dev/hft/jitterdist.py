# from jitterstat, get distribution of stdev

import sys

# usage jitterdist distfile

binunit = 0.1
dist = {}
for line in open(sys.argv[1]):
    tmp = line.split()
    stdev = float(tmp[4])
    binnum = int(stdev/binunit)
    dist.setdefault(binnum, 0)
    dist[binnum] = dist[binnum] + 1

binnumset = dist.keys()
binnumset.sort()
for b in binnumset:
    print b*binunit, dist[b]
