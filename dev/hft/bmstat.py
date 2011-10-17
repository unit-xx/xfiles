import sys, math
import numpy as np

BINSIZE = 5

def roundn(n, bound):
    return int(math.floor(n/bound)*bound)

def main():
    earns = []
    for line in open(sys.argv[1]):
        if line.find('PL') != -1:
            earn = float(line.split(',')[1].split()[0])
            earns.append(earn)
    earns = np.array(earns)
    emin = roundn(np.amin(earns), BINSIZE)
    emax = roundn(np.amax(earns), BINSIZE) + 3*BINSIZE
    hist, edge = np.histogram(earns, np.arange(emin, emax, BINSIZE))
    print emin, emax
    print sorted(earns)
    print hist, edge
    for i, v in enumerate(hist):
        print edge[i], hist[i]


if __name__=="__main__":
    main()
