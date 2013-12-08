import random
import operator

def rrpath(rf, sig, dt, T):
    ret = []
    nstep = int(T/dt)
    for i in xrange(nstep):
        rday = rf * dt + sig * (dt**0.5) * random.gauss(0, 1)
        ret.append(rday)
    return ret

def accumulate(iterable, func=operator.add):
    'Return running totals'
    # accumulate([1,2,3,4,5]) --> 1 3 6 10 15
    # accumulate([1,2,3,4,5], operator.mul) --> 1 2 6 24 120
    it = iter(iterable)
    total = next(it)
    yield total
    for element in it:
        total = func(total, element)
        yield total

def swEDpath(t0, s0, dt, T, rf, sig, r):
    '''
    swsy base, as a GBM starting at (t0, s0), walks to the end
    of T years. Walking step in dt time, risk free rate rf,
    volatility sig. Earn r at the end of each year, if ED
    condition is satisfied.
    '''

    step = int(t0/dt)
    t0 = step * dt
    s0 = s0 * 2

    rrp = rrpath(rf, sig, dt, T-t0+dt)
    # sw base has return rate of 95% * tracked index.
    rrp = [x*0.95 for x in rrp]
    nstep = len(rrp)
    edstep = int(1/dt)
    svalue = s0
    edcount = 1
    edpath = []

    for rr in rrp:
        step += 1
        svalue = svalue * (1+rr)

        if step == edstep:
            if (svalue - (1+edcount*r)) > 0.1:
                ed = edcount * r
                edpath.append(ed)
                svalue = svalue - edcount*r
                edcount = 1
            else:
                edpath.append(0.0)
                edcount += 1

            step = 0

    return edpath

def NPV(edpath, R, t0):
    edpath.reverse()
    ret = 0.0
    for x in edpath:
        ret = (ret + x)/(1+R)
    ret = ret * (1+R*t0)
    return ret

def swsyvalue(t0, s0, dt, T, rf, sig, r, R, N=100):
    ret = 0.0
    for i in xrange(N):
        edp = swEDpath(t0, s0, dt, T, rf, sig, r)
        npv = NPV(edp, R, t0)
        ret += npv
    ret = ret / N

    return ret

def frange(start, stop, step):
    eps = 1e-8
    r = start
    while stop-r >= eps:
        # TODO: better inequation.
    	yield r
    	r += step
