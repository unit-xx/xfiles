# feed siqyyyymmdd.log through registered filters.
# this is a library defining filters, etc.

import math

class filter:
    def __init__(self):
        self._value = None
        # used for manage sub-filters
        self.fset = set()
        self.fmap = {}

    def value(self):
        return self._value

    def feed(self, x):
        # sub class implement this method.
        # it may simply compute _value on data x, or
        # compose complex graphs with sub-filters
        raise Exception("not implemented.")

    def add(self, f, name=None):
        # add subfilters
        self.fset.add(f)
        if name is not None:
            if name in self.fmap:
                raise Exception("fitler with duplicated name.")
            else:
                self.fmap[name] = f

class filtermgr(filter):
    # a filter manager simply passes data to sub-filters.
    def feed(self, x):
        for f in self.fset():
            f.feed(x)

class FuncFilter(filter):
    def __init__(self, func):
        filter.__init__(self)
        self.func = func

    def feed(self, x):
        self._value = self.func(x)

class DiffRatioFilter(filter):
    def __init__(self):
        filter.__init__(self)
        self.lastv = None

    def feed(self, x):
        if self.lastv is not None:
            try:
                self._value = x/float(self.lastv) - 1
            except ZeroDivisionError:
                self._value = float("Inf")
        self.lastv = x

class MedianFilter(filter):
    def __init__(self, slen):
        filter.__init__(self)
        self.slen = slen
        self.medpos = -(int)(slen/2)
        self.vbuf = []

    def feed(self, x):
        # update _value and truncate data
        self.vbuf.append(x)
        del self.vbuf[0:-self.slen]
        self.vbuf.sort()
        if len(self.vbuf) >= self.slen:
            self._value = self.vbuf[self.medpos]

class EMAFilter(filter):
    def __init__(self, lmbda):
        filter.__init__(self)
        self.lmbda = lmbda
        self._value = None

    def feed(self, x):
        try:
            self._value = self._value*(1-self.lmbda) + x*self.lmbda
        except TypeError:
            self._value = x

class EMVariance(filter):
    def __init__(self, lmbda):
        filter.__init__(self)
        self.lmbda = lmbda
        self._value = None
        self.p = None
        self.p2 = None

    def feed(self, x):
        try:
            self.p = self.p*(1-self.lmbda) + x*self.lmbda
            self.p2 = self.p2*(1-self.lmbda) + x*x*self.lmbda
        except TypeError:
            self.p = x
            self.p2 = x**2
        self._value = self.p2 - self.p**2

class WMAFilter(filter):
    TRUNCMAX = 4
    def __init__(self, slen, delay=0):
        filter.__init__(self)
        self.trunclimit = self.TRUNCMAX * slen
        self.slen = slen
        self.delay = delay
        self.vbuf = []
        self.wbuf = []
        self.vwbuf = []
        self.vwsum = 0.0
        self.wsum = 0.0

    def feed(self, x):
        v = x[0]
        w = x[1]
        vw = v*w

        # compute and append
        if len(self.vbuf) >= self.slen:
            # incrementally compute
            self.wsum = self.wsum - self.wbuf[-self.slen] + w
            self.vwsum = self.vwsum - self.vwbuf[-self.slen] + vw
            try:
                self._value = self.vwsum/float(self.wsum)
            except ZeroDivisionError:
                self._value = 0.0

        # append and update value for the first time, in case ...
        self.vbuf.append(v)
        self.wbuf.append(w)
        self.vwbuf.append(vw)
        if len(self.vbuf) == self.slen:
            # first evaluation
            self.wsum = sum(self.wbuf)
            self.vwsum = sum(self.vwbuf)
            try:
                self._value = self.vwsum/float(self.wsum)
            except ZeroDivisionError:
                self._value = 0.0

        # trunt data
        if len(self.vbuf) > self.trunclimit:
            del self.vbuf[0:-self.slen]
            del self.wbuf[0:-self.slen]
            del self.vwbuf[0:-self.slen]

class VarianceFilter(filter):
    def __init__(self, slen):
        filter.__init__(self)
        f = WMAFilter(slen)
        self.add(f, "p")
        f2 = WMAFilter(slen)
        self.add(f2, "p2")

    def feed(self, x):
        v = x[0]
        w = x[1]
        self.fmap["p"].feed(x)
        v2 = v*v
        self.fmap["p2"].feed((v2, w))

        vp = self.fmap["p"].value()
        vp2 = self.fmap["p2"].value()
        try:
            self._value = vp2 - vp*vp
        except TypeError:
            #vp2 or vp maybe none if feeded with not enough data
            pass

class CovFillter(filter):
    def __init__(self, slen):
        filter.__init__(self)
        f = WMAFilter(slen)
        self.add(f, "x")
        f2 = WMAFilter(slen)
        self.add(f2, "y")
        f3 = WMAFilter(slen)
        self.add(f3, "xy")

    def feed(self, data):
        x = data[0]
        y = data[1]
        self.fmap["x"].feed((x,1))
        self.fmap["y"].feed((y,1))
        self.fmap["xy"].feed((x*y,1))
        try:
            self._value = self.fmap["xy"].value() - self.fmap["x"].value()*self.fmap["y"].value()
        except TypeError:
            # value maybe none if feeded with not enough data
            pass

class DirectionFilter(filter):
    def __init__(self, slen):
        filter.__init__(self)
        f = CovFillter(slen)
        self.add(f, "cov")
        f2 = VarianceFilter(slen)
        self.add(f2, "xvar")
        f3 = VarianceFilter(slen)
        self.add(f3, "yvar")

    def feed(self, data):
        x = data[0]
        y = data[1]
        self.fmap["cov"].feed((x,y))
        self.fmap["xvar"].feed((x,1))
        self.fmap["yvar"].feed((y,1))
        try:
            cov = self.fmap["cov"].value()
            if cov < 1e-6 and cov > -1e-6:
                beta = 0.0
                corr = 0.0
            else:
                beta = self.fmap["cov"].value()/self.fmap["xvar"].value()
                corr = self.fmap["cov"].value()/math.sqrt(self.fmap["xvar"].value()* self.fmap["yvar"].value())
            # a hack into VarianceFilter to get average value
            xavg = self.fmap["xvar"].fmap["p"].value()
            yavg = self.fmap["yvar"].fmap["p"].value()
            alpha = yavg - beta*xavg
            self._value = (alpha, beta, corr)
        except TypeError:
            pass

if __name__=="__main__":
    import time
    print "before import", time.time()
    import random
    from scipy import stats
    import numpy

    slen = 3
    vbuf = []
    wbuf = []
    vwbuf = []
    v2wbuf = []
    wmaf = WMAFilter(slen)
    vf = VarianceFilter(slen)
    covf = CovFillter(slen)
    dirf = DirectionFilter(slen)
    start = time.time()
    print "after import", start
    for i in range(2*slen):
        w = random.random()*10
        #w = i
        v = random.random()*10
        #v = w*2
        vbuf.append(v)
        wbuf.append(w)
        vwbuf.append(v*w)
        v2wbuf.append(v*v*w)
        wmaf.feed((v,w))
        vf.feed((v,w))
        covf.feed((v,w))
        dirf.feed((v,w))

    print "test WMAFilter:",
    vwsum = sum(vwbuf[-slen:])
    wsum = sum(wbuf[-slen:])
    vavg = vwsum/wsum
    print (wmaf.value() - vavg) < 1e-10

    print "test VarianceFilter:",
    v2wsum = sum(v2wbuf[-slen:])
    v2avg = v2wsum/wsum
    vvar = v2avg - vavg*vavg
    print (vf.value() - vvar) < 1e-10

    print "test CovFillter:",
    vsum = sum(vbuf[-slen:])
    cov = vwsum/slen - vsum*wsum/slen/slen
    print (covf.value() - (cov)) < 1e-10

    print "test DirectionFilter:",
    x = numpy.array(vbuf[-slen:])
    y = numpy.array(wbuf[-slen:])
    slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)
    beta, corr = dirf.value()
    print beta, corr
    print (beta - slope < 1e-10) and (corr-r_value < 1e-10)

    end = time.time()
    print "end time", end
    print "time cost: %.2f" % (end-start)
