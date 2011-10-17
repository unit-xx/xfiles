# analyze trading volumn of HS300 futures.

import sys
import math
from siffilter import *

# decay factor in EMA
alpha = 0.03
fn = sys.argv[1]
target = "1108"

volema = EMAFilter(alpha)
volma = WMAFilter(3600)
volvar = VarianceFilter(3600)
dvlast = 0
lc = 0

for line in open(fn):
    t = line.split()
    if len(t) == 0:
        break

    if len(t) != 12:
        continue

    if t[3] == "IF" and t[4] == target:
        lc += 1
        dvnew = int(t[6])
        pp = (t[5])
        dv = dvnew - dvlast
        dvlast = dvnew
        volema.feed(dv)
        volma.feed((dv,1))
        volvar.feed((dv,1))

        if volma.value() is not None:
            print lc, pp, dv, volema.value(), volma.value(),
            sigma = math.sqrt(volvar.value())
            print sigma,
            if (volema.value() - volma.value()) > 0.5*sigma:
                print 1
            else:
                print -1

