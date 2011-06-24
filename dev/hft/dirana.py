import sys
import random
import time

from siffilter import *

slen = int(sys.argv[1])
fn = sys.argv[2]

df = DirectionFilter(slen)
maf = WMAFilter(slen*4)

lc = 0
start = time.time()
for line in open(fn):
    t = line.split()
    if len(t) == 0:
        break

    if len(t) != 12:
        continue

    lc = lc + 1
    p = float(t[5])
    df.feed((lc, p))
    if df.value() is not None:
        beta, corr = df.value()
        maf.feed((corr**2, 1))
        if maf.value() is not None:
            print lc, maf.value()

end = time.time()
print end-start
