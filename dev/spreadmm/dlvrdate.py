# given a contracts range, calculate the deliver dates.
# Usage: dlvrdate 1206 1301

import sys
from util import *

if(len(sys.argv) <= 2):
    print "Usage: %s startdate endate, e.g. %s 1209 1301" % (sys.argv[0], sys.argv[0])
    sys.exit(1)

ym = sys.argv[1]
startym = (2000+int(ym[0:2]), int(ym[2:4]))
ym = sys.argv[2]
endym = (2000+int(ym[0:2]), int(ym[2:4]))

ym = startym
ifc = IFCalendar()
while(ym <= endym):
    dlvday = ifc.dlvrday(ym)
    print '%02d%02d'%(ym[0]-2000,ym[1]), dlvday
    ym = incmonth(ym)
