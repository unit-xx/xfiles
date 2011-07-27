import sys
import random
import math

from siffilter import *

from scipy import stats
import numpy


slen = 10

vf = VarianceFilter(slen)
df = DirectionFilter(slen)
maf = WMAFilter(slen)

xbuf = []
ybuf = []
for i in range(slen*1):
    #x = random.random()*10
    x = i
    y = random.random()*10
    xbuf.append(x)
    ybuf.append(y)
    vf.feed((x,1))
    df.feed((x,y))
    xa = numpy.array(xbuf[-slen:])
    ya = numpy.array(ybuf[-slen:])
    if df.value() is not None:
        alpha, beta, corr = df.value()
        slope, intercept, r_value, p_value, std_err = stats.linregress(xa,ya)
        slope2, intercept2, r_value2, p_value2, std_err2 = stats.linregress(ya,xa)
        print "lnreg:"
        print alpha, beta, corr
        print intercept, slope, r_value
        print intercept2, slope2, r_value2
        print slope2*slope
        print

    if vf.value() is not None:
        print vf.value()
        print xa.var()
        print xa
        print

sys.exit(1)

for i in range(slen):
    vf.feed((10,1))
    maf.feed((10,1))

print vf.value(), maf.value()

for i in range(slen):
    vf.feed((20,1))
    maf.feed((20,1))
    print math.sqrt(vf.value()), maf.value()


