import sys
import math
from decimal import *
from datetime import datetime, timedelta

f = open(sys.argv[1])

maxlongpos = 1
maxshortpos = 1
longdeals = []
shortdeals = []
longs = []
shorts = []
openthr = Decimal('0.7')
openvarthr = 1.0
closetol = Decimal('0.0')
stoploessthr = Decimal('0.5')
holdinterval = timedelta(0, 4, 000000)

"""
1. how many concurrent opens?
2. a quote can be used for both open and close?
3. how long should an open last?
"""

def toseconds(duration):
    return duration.seconds + duration.microseconds/1000000.0

def makerec(t):
    timefmt1 = "%H:%M:%S.%f"
    timefmt2 = "%H:%M:%S"
    try:
        ret = [t[0], datetime.strptime(t[1], timefmt1)]
    except ValueError:
        ret = [t[0], datetime.strptime(t[1], timefmt2)] 
    ret[2:] = [Decimal(x) for x in t[2:]]
    return ret

while 1:
    t = f.readline().split()
    if len(t) == 0:
        break

    if len(t) != 15:
        continue

    t = makerec(t)
    p = t[2]

    # add opens for short and long
    if len(shorts) < maxshortpos:
        #if t[5] > openthr and t[6] > openthr and t[7] > openthr:
        if t[4] > openthr and t[4] > Decimal('1.5')*t[10]:
            #toearn = Decimal("%.1f"%(math.floor(min(t[5:8])*5)/5))
            toearn = t[4]
            #open, close, [open price, toclose price, close price(filled later)]
            shorts.append([t, None, [p, p-toearn, None]]) 

    if len(longs) < maxlongpos:
        #if t[5] < -openthr and t[6] < -openthr and t[7] < -openthr:
        if -t[4] > openthr and -t[4] > Decimal('1.5')*t[10]:
            #toearn = Decimal("%.1f"%(math.floor(-max(t[5:8])*5)/5))
            toearn = -t[4]
            longs.append([t, None, [p, p+toearn, None]])
    # look for close opportunity.
    toremove = []
    for x in shorts:
        if p <= x[2][1]+closetol or t[1]-x[0][1] > holdinterval or p > x[2][0]+stoploessthr:
            toremove.append(x)
            shortdeals.append(x)
            x[1] = t
            x[2][2] = p
    for x in toremove:
        shorts.remove(x)

    toremove = []
    for x in longs:
        if p >= x[2][1]-closetol or t[1]-x[0][1] > holdinterval or p < x[2][0]-stoploessthr:
            toremove.append(x)
            longdeals.append(x)
            x[1] = t
            x[2][2] = p
    for x in toremove:
        longs.remove(x)

print "=== dealed shorts %d ===" % len(shortdeals)
print "=== undealed shorts %d ===" % len(shorts)
print "=== dealed longs %d ===" % len(longdeals)
print "=== undealed longs %d ===" % len(longs)

print
print "=========================================="
print

print "=== dealed shorts %d ===" % len(shortdeals)
for x in shortdeals:

    duration = x[1][1] - x[0][1]
    # opent, closet, open price, close price, hold time, toearn, act earn, 
    print x[0][1].time(), x[1][1].time(), x[0][2], x[1][2], toseconds(duration), x[2][0]-x[2][1], x[2][0]-x[2][2]
    #print x[0][1].time(), x[1][1].time(), x[0][8], x[1][8], toseconds(duration), x[2][0]-x[2][1], x[2][0]-x[2][2], x[0][9], x[0][10], x[0][11], x[0][5], x[0][6], x[0][7]

print "=== undealed shorts %d ===" % len(shorts)
for x in shorts:
    print x

print "=== dealed longs %d ===" % len(longdeals)
for x in longdeals:
    duration = x[1][1] - x[0][1]
    print x[0][1].time(), x[1][1].time(), x[0][2], x[1][2], toseconds(duration), x[2][1]-x[2][0], x[2][2]-x[2][0]
    #print x[0][1].time(), x[1][1].time(), x[0][8], x[1][8], toseconds(duration), x[2][1]-x[2][0], x[2][2]-x[2][0], x[0][9], x[0][10], x[0][11], x[0][5], x[0][6], x[0][7]

print "=== undealed longs %d ===" % len(longs)
for x in longs:
    print x
