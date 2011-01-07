import sys
from datetime import datetime

f = open(sys.argv[1])

longdeals = []
shortdeals = []
longs = []
shorts = []
openmax = 100
openthr = 0.5

while 1:
    t = f.readline().split()
    if len(t) == 0:
        break

    if len(t) != 9:
        continue

    t[2:] = [float(x) for x in t[2:]]

    # add opens for short and long
    if t[5] > openthr and t[6] > openthr and t[7] > openthr:
        toearn = min(t[5:8])
        t.append(t[8]-toearn)
        shorts.append(t)

    if t[5] < -openthr and t[6] < -openthr and t[7] < -openthr:
        toearn = max(t[5:8])
        t.append(t[8]-toearn)
        longs.append(t)

    # look for close opportunity.
    p = t[8]
    toremove = []
    for x in shorts:
        if p <= x[9]:
            toremove.append(x)
            shortdeals.append((x,t))
    for x in toremove:
        shorts.remove(x)

    toremove = []
    for x in longs:
        if p >= x[9]:
            toremove.append(x)
            longdeals.append((x,t))
    for x in toremove:
        longs.remove(x)

print "=== dealed shorts %d ===" % len(shortdeals)
print "=== undealed shorts %d ===" % len(shorts)
print "=== dealed longs %d ===" % len(longdeals)
print "=== undealed longs %d ===" % len(longs)

print
print "=========================================="
print

timefmt = "%H:%M:%S.%f"
print "=== dealed shorts %d ===" % len(shortdeals)
for x in shortdeals:

    duration = datetime.strptime(x[1][1], timefmt) - datetime.strptime(x[0][1], timefmt)
    print x[0][1], x[1][1], x[0][8], x[1][8], duration.seconds, x[0][8]-x[1][8], x[0][8]-x[0][9]

print "=== undealed shorts %d ===" % len(shorts)
for x in shorts:
    print x

print "=== dealed longs %d ===" % len(longdeals)
for x in longdeals:
    duration = datetime.strptime(x[1][1], timefmt) - datetime.strptime(x[0][1], timefmt)
    print x[0][1], x[1][1], x[0][8], x[1][8], duration.seconds, x[1][8]-x[0][8], x[0][9]-x[0][8]

print "=== undealed longs %d ===" % len(longs)
for x in longs:
    print x
