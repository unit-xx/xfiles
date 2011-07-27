# stock alpha/beta with base index
import sys

from siffilter import *

a=1
b=9

drfa = DiffRatioFilter()
drfb = DiffRatioFilter()
df = DirectionFilter(20)

for line in open(sys.argv[1]):
    if line.startswith("#"):
        continue

    tmp = line.split()
    va = float(tmp[a])
    vb = float(tmp[b])
    #vbs = [float(x) for x in tmp[1:]]
    #vb = sum(vbs)/len(vbs)

    drfa.feed(va)
    drfb.feed(vb)
    if drfa.value() is not None and drfb.value() is not None:
        df.feed((drfa.value(), drfb.value()))
        if df.value() is not None:
            alpha, beta, corr = df.value()
            print tmp[0], alpha, beta, corr, drfa.value(), drfb.value(), drfa.value()*beta+alpha
