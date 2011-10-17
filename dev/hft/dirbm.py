import sys
from siffilter import CovFillter

track = []
posopen = False
# NOTE: form a trend open, trend reaches max close
# NOTE: wait corr approach zero after close
waitforopen = True

for line in open(sys.argv[1]):
    t = line.split()
    if len(t) != 15:
        continue

    tick = int(t[0])
    date, time = t[1:3]
    beta, corr, betalong, corrlong, mafbete, p, \
            dv, dvmalong, \
            dvma, dvsgm, dvmed, bcbeta, bccorr, basprd= \
            [float(x) for x in t[3:]]

    if posopen:
        # try close
        #bcthr = 0.02
        #if beta > -bcthr and beta < bcthr:
        pos = track[-1]
        ccthr = 20.0/100
        diff = corr - pos["cmax"]
        if diff > 0:
            pos["cmax"] = corr
        else:
            if diff/pos["cmax"] < -ccthr:
                pos["ct"] = tick
                pos["cp"] = p
                posopen = False
    else:
        # try open
        if waitforopen:
            if corr < 0.1:
                waitforopen = False
        else:
            bothr = 0.05
            cothr = 0.5
            if corr > cothr and ((beta > bothr) or (beta < -bothr)):
                pos = {}
                if beta > 0:
                    pos["dir"] = 1
                else:
                    pos["dir"] = -1
                pos["op"] = p
                pos["ot"] = tick
                pos["cmax"] = corr
                track.append(pos)
                posopen = True
                waitforopen = True

earn = 0.0
nonclosed = []
for p in track:
    try:
        earn = earn + p["dir"] * (p["cp"]-p["op"])
    except KeyError:
        nonclosed.append(p)

for p in track:
    try:
        earn = p["dir"] * (p["cp"]-p["op"])
        dur = p["ct"]-p["ot"]
        print "%2d\t%d,%.1f => %d,%.1f\t%d,%.1f" % (p["dir"], 
                p["ot"], p["op"], p["ct"], p["cp"], dur, earn)
    except KeyError:
        pass

print "opened position, earning, earning after fee"
print len(track), earn, earn-len(track)*0.4
print
print "Still open"
print nonclosed
print

# arrow file for plot positions by gnuplot
try:
    f = open(sys.argv[2], "w")
    for p in track:
        try:
            print >>f, "set arrow from %d,%.1f to %d,%.1f nohead lw 2" % (p["ot"],
                    p["op"], p["ct"], p["cp"]),
            if p["dir"] > 0:
                print >>f, "lc rgb 'red'"
            else:
                print >>f, "lc rgb 'blue'"

            print >>f, "set arrow from %d,%.1f to %d,%.1f nohead lw 3" % (p["ot"],
                    0.0, p["ct"], 0.0),
            if p["dir"] > 0:
                print >>f, "lc rgb 'red'"
            else:
                print >>f, "lc rgb 'blue'"
        except KeyError:
            pass
except IndexError:
    pass

# NOTE: 
# - find a trend then follow,
# - consider change rate of corr
# - double check trend in long and short terms
# - don't close while not breaking close line, or has volume support.
# 
