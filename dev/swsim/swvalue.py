import os
import sys
import csv

from itertools import product

from simlib import *

if os.path.exists(sys.argv[1]):
    if 'y' != raw_input('Overwrite existing file? '):
        sys.exit(1)

t0 = 0.0
s0 = 0.7
dt = 0.01
T = 200.0
rf = 0.04
sig = 0.25
r = 0.06
R = 0.065

s0rng = frange(0.3, 1.21, 0.01)
sigrng = frange(0.2, 0.36, 0.01)

fullrng = product(s0rng, sigrng)

rst = []
i = 0
rnglen = len(s0rng) * len(sigrng)
for rtuple in fullrng:
    i = i + 1
    s0, sig = rtuple
    print '(%d/%d) %.2f, %.2f,' % (i, rnglen, s0, sig),
    v = swsyvalue(t0, s0, dt, T, rf, sig, r, R)
    print v
    rst.append((s0, sig, v))

f = open(sys.argv[1], 'w')
writer = csv.writer(f)
writer.writerow(('s0', 'sig', 'value'))
for row in rst:
    writer.writerow(row)
f.close()
