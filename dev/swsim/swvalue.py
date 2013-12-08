import os
import sys

from simlib import *

if os.path.exists(sys.argv[1]):
    if 'y' != raw_input('Overwrite existing file? '):
        sys.exit(1)

t0 = 0.0
s0 = 0.7
dt = 0.01
T = 100.0
rf = 0.04
sig = 0.25
r = 0.06
R = 0.065

s0rng = frange(0.3, 1.21, 0.05)
sigrng = frange(0.2, 0.36, 0.01)

rst = []
for s0 in s0rng:
    for sig in sigrng:
        v = swsyvalue(t0, s0, dt, T, rf, sig, r, R)
        rst.append((s0, sig, v))

f = open(sys.argv[1], 'w')
writer = csv.writer(f)
writer.writerow(('s0', 'sig', 'value'))
for row in rst:
    writer.writerow(row)
f.close()
