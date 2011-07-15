import sys
import random
import math

from siffilter import *

from scipy import stats
import numpy

xbuf = []
vf = VarianceFilter(60)
maf = WMAFilter(60)
for line in open(sys.argv[1]):
    tp = line.split()
    dv = float(tp[5])
    xbuf.append(dv)
    vf.feed((dv,1))
    maf.feed((dv,1))
    xbuf.append(dv)

xa = numpy.array(xbuf)
if vf.value() is not None:
    print xa.var(), vf.value()

print xa.mean(), maf.value()
