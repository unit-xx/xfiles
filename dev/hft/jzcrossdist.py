# from jitterstat, get distribution of stdev

import sys

# usage jitterdist distfile

binunit = 1
dist = {}
for line in open(sys.argv[1]):
    if line.startswith("#"):
        continue

    tmp = line.split()
    zcross = int(tmp[7])
    binnum = int(zcross/binunit)
    dist.setdefault(binnum, 0)
    dist[binnum] = dist[binnum] + 1

binnumset = dist.keys()
binnumset.sort()
for b in binnumset:
    print b*binunit, dist[b]
