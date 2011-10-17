# direction analysis of HS300 futures
# data source: siqyyyymmdd.log
import sys
import random
import time
import math

from siffilter import *

slen = int(sys.argv[1])
fn = sys.argv[2]
TARGET = "1108"

df = DirectionFilter(slen)
dflong = DirectionFilter(2*slen)
df2 = DirectionFilter(slen)
mafbeta = WMAFilter(slen)
mafdv = WMAFilter(slen)
mafdvlong = WMAFilter(20*120)
meddv = MedianFilter(slen)
vardv = VarianceFilter(slen)

mafprice = WMAFilter(30)

lc = 0
start = time.time()
dvaccu = 0
for line in open(fn):
    t = line.split()
    if len(t) == 0:
        break

    if len(t) != 12:
        continue

    if t[3] == "IF" and t[4] == TARGET:

        lc = lc + 1
        pp = float(t[5])
        mafprice.feed((pp,1))
        p = mafprice.value()
        if p is not None:
            dv = int(t[6]) - dvaccu
            dvaccu = int(t[6])
            df.feed((lc, p))
            dflong.feed((lc,p))
            mafdv.feed((dv, 1))
            mafdvlong.feed((dv, 1))
            meddv.feed(dv)
            vardv.feed((dv, 1))
            if dflong.value() is not None and mafprice.value() is not None:
                alpha, beta, corr = df.value()
                alphalong, betalong, corrlong = dflong.value()
                df2.feed((beta, corr))
                mafbeta.feed((beta, 1))
                if mafbeta.value() is not None and mafdvlong.value() is not None:
                    dd = t[0]
                    tt = t[1]
                    print dd, tt, lc, beta, corr, betalong, corrlong, mafbeta.value(), \
                            p, dv, mafdvlong.value(), mafdv.value(), \
                            math.sqrt(vardv.value()), meddv.value(),
                    if df2.value() is not None:
                        alpha2, beta2, corr2 = df2.value()
                        print beta2, corr2,
                    else:
                        print 0, 0,
                    print float(t[10]) - float(t[8]) # bid-ask spread

end = time.time()
print end-start

# NOTE: baspread, ba volumn ratio
