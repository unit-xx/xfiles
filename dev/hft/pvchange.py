# price and trading volume change analysis

import sys, os
import math

import util
from siffilter import *


fn = sys.argv[1]
bfn = os.path.basename(fn)
TARGET = util.calsicontracts(bfn[3:-4])[0]

lastpp = 0.0
lastpp2 = 0.0
lastdv = 0
lc = 0

ql1 = 960
ql2 = 1920#600*1.618
ql3 = 3840
ql4 = 7680#1920*1.618
q1 = 1-math.pow(0.5, 1.0/ql1)
q2 = 1-math.pow(0.5, 1.0/ql2)
q3 = 1-math.pow(0.5, 1.0/ql3)
q4 = 1-math.pow(0.5, 1.0/ql4)

ef = EMAFilter(q1)
ef2 = EMAFilter(q2)
ef3 = EMAFilter(q3)
ef4 = EMAFilter(q4)

#ev = EMVariance(q1)
#ev2 = EMVariance(q2)


#qp = 0.618**8
qp2 = 1-math.pow(0.5, 1.0/240)
qp = 1-math.pow(0.5, 1.0/120)
qp3 = 1-math.pow(0.5, 1.0/960)
pef = EMAFilter(qp2)
pev = EMVariance(qp)
pevem = EMAFilter(qp3)
pv = VarianceFilter(240)
pvavg = WMAFilter(3600)

eps = 5e-8
qh1 = 1-math.pow(0.5, 1.0/ql1)
qh2 = 1-math.pow(0.5, 1.0/ql3)
hitem1 = EMAFilter(qh1)
hitem2 = EMAFilter(qh2)
hstate1 = 0
hstate2 = 0

ppchange = 0.0
ppchange2 = 0.0
pp2 = 0.0

for line in open(fn):
    t = line.split()
    if len(t) == 0:
        break

    if len(t) != 12:
        continue

    if t[3] == "IF" and t[4] == TARGET:

        lc = lc + 1
        pp = float(t[5])
        dvaccu = int(t[6])
        dv = dvaccu - lastdv

        if t[2] >= "09:14:00":
            pef.feed(pp)
            pp2 = pef.value()
            pev.feed(pp2)
            evpp = math.sqrt(pev.value())
            pevem.feed(evpp)
            evem = pevem.value()

            pv.feed((pp,1))
            if pv.value():
                pvavg.feed((math.sqrt(pv.value()),1))

            try:
                ppchange = (pp - lastpp)/lastpp
                ppchange2 = (pp2 - lastpp2)/lastpp2
            except ZeroDivisionError:
                pass

            ef.feed(ppchange2)
            ef2.feed(ppchange2)
            ef3.feed(ppchange2)
            ef4.feed(ppchange2)
            #ev.feed(ppchange2)
            #ev2.feed(ppchange2)
            print lc, pp, pp2, ppchange, dv, "%.2f"%(ppchange*dv), ef.value(), ef2.value(), ef3.value(), ef4.value(), evpp, evem, #, ev.value(), ev2.value()

            if pv.value():
                print math.sqrt(pv.value()),
            else:
                print 0.0,

            if pvavg.value():
                print pvavg.value(),
            else:
                print 0.0,

            if ef.value() - ef2.value() > eps:
                if hstate1 == -1:
                    hitem1.feed(1/hitem1.lmbda)#ql1/hitem1.lmbda)
                else:
                    hitem1.feed(0)
                hstate1 = 1
            elif ef.value() - ef2.value() < -eps:
                if hstate1 == 1:
                    hitem1.feed(1/hitem1.lmbda)#ql1/hitem1.lmbda)
                else:
                    hitem1.feed(0)
                hstate1 = -1
            else:
                hitem1.feed(0)

            if ef3.value() - ef4.value() > eps:
                if hstate2 == -1:
                    hitem2.feed(1/hitem2.lmbda)#ql3/hitem2.lmbda)
                else:
                    hitem2.feed(0)
                hstate2 = 1
            elif ef3.value() - ef4.value() < -eps:
                if hstate2 == 1:
                    hitem2.feed(1/hitem2.lmbda)#ql3/hitem2.lmbda)
                else:
                    hitem2.feed(0)
                hstate2 = -1
            else:
                hitem2.feed(0)

            print hitem1.value(), hitem2.value()

        lastpp = pp
        lastpp2 = pp2
        lastdv = dvaccu

        #if t[2] > "09:50:00":
            #if ef.value() is not None:

