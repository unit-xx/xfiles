import sys, os
import operator

EPS = 1e-7
vath = 1.2+EPS

def open1(*args):
    ls, ef1, ef2, ef3, ef4 = args[0:5]
    if ls == 1:
        op = operator.gt
        tbar = EPS
    else:
        op = operator.lt
        tbar = -EPS

    return op(ef4, 2*tbar) and op((ef3-ef4), 0.5*tbar) and op((ef1-ef2), tbar) # vadpp < vath:

def close1(*args):
    ls, ef1, ef2, ef3, ef4 = args[0:5]
    if ls == 1:
        op = operator.lt
        tbar = -EPS
    else:
        op = operator.gt
        tbar = EPS

    return op((ef2-ef3), tbar/2)# and vadpp < vath:

def open2(*args):
    ls, ef1, ef2, ef3, ef4, pv, evpp, hit1, hit2 = args[0:9]
    return open1(*args) and pv < 1.2 and evpp < 1 and hit2 < 0.5

def close2(*args):
    ls, ef1, ef2, ef3, ef4, pv, evpp, hit1, hit2 = args[0:9]
    return close1(*args)

openp = open2
closep = close2

def main():
    trace = []
    cpos = []

    for line in open(sys.argv[1]):
        lc, pp, pp2, ppchange, dv, ppchangemdv, ef1, ef2, ef3, ef4, evpp, evem, pv, pvavg, hit1, hit2 = [float(x) for x in line.split()]

        if lc < 600:
            continue

        vadpp = evpp/evem

        if cpos == []:
            # look for open
            if openp(1, ef1, ef2, ef3, ef4, pv, evpp, hit1, hit2):
                # open long
                cpos.append(1)
                cpos.append(lc)
                cpos.append(pp)
            elif openp(-1, ef1, ef2, ef3, ef4, pv, evpp, hit1, hit2):
                #and (ef2-ef3) < -EPS 
                cpos.append(-1)
                cpos.append(lc)
                cpos.append(pp)
        else:
            if closep(cpos[0], ef1, ef2, ef3, ef4, pv, evpp, hit1, hit2):
                cpos.append(lc)
                cpos.append(pp)
                trace.append(cpos)
                cpos = []

    earn = 0.0
    for p in trace:
        earn += p[0] * (p[4]-p[2])

        print >>sys.stdout, "set arrow from %d,%.1f to %d,%.1f nohead lw 2" % (p[1],
                p[2], p[3], p[4]),
        if p[0] > 0:
            print >>sys.stdout, "lc rgb 'red'"
        else:
            print >>sys.stdout, "lc rgb 'dark-green'"

    print >>sys.stderr, "%d trades, %.2f PL." % (len(trace), earn)

    if cpos != []:
        print >>sys.stderr, "open trade: %s" % str(cpos)
        if cpos[0] > 0:
            print >>sys.stdout, "set object circle center %d,%.1f size 50 front fc rgb 'red' fs solid" % (cpos[1], cpos[2])
        else:
            print >>sys.stdout, "set object circle center %d,%.1f size 50 front fc rgb 'green' fs solid" % (cpos[1], cpos[2])

    print >>sys.stdout, "set label '%s: %d trades, %.2f PL, unclosed T %s' at screen 0.382, 1.0 center" % (os.path.basename(sys.argv[1]),
        len(trace), earn, str(cpos))
    

if __name__=="__main__":
    main()



