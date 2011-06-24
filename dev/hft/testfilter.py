import sys
import random

from siffilter import *

from scipy import stats
import numpy


slen = 4

vf = VarianceFilter(slen)
df = DirectionFilter(slen)

xbuf = []
ybuf = []
for i in range(slen*1):
    #x = random.random()*10
    x = i
    y = random.random()*10
    xbuf.append(x)
    ybuf.append(y)
    vf.feed((x,1))
    #df.feed((x,y))
    xa = numpy.array(xbuf[-slen:])
    ya = numpy.array(ybuf[-slen:])
    if df.value() is not None:
        beta, corr = df.value()
        slope, intercept, r_value, p_value, std_err = stats.linregress(xa,ya)
        #print beta, corr
        #print slope, r_value
        #print

    if vf.value() is not None:
        print vf.value()
        print xa.var()
        print xa
