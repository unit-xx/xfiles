import os, sys, glob, gzip
from datetime import datetime, timedelta

from siffilter import *

scodefn = sys.argv[1]
# analysis windows size
wsize = int(sys.argv[2])
stockqdir = sys.argv[3]

def sampledavg(qfile, scodes, sintval=timedelta(0,1800)):
    year = int(qfile[-15:-11])
    month = int(qfile[-11:-9])
    day = int(qfile[-9:-7])
    qday = datetime(year, month, day)
    # pass Saturday and Sunday
    if qday.weekday() in (5,6):
        #print s
        return None

    # calculate the sample timestamps
    amstart = datetime(year, month, day, 9, 30, 0)
    amend = datetime(year, month, day, 11, 30, 0)
    pmstart = datetime(year, month, day, 13, 0, 0)
    pmend = datetime(year, month, day, 15, 0, 0)
    samplets = []
    ts = amstart
    while ts >= amstart and ts <= amend:
        # the morning period
        samplets.append(ts)
        ts = ts + sintval
    ts = pmstart
    while ts >= pmstart and ts <= pmend:
        # the afternoon period
        samplets.append(ts)
        ts = ts + sintval
    #print samplets

    f = gzip.open(qfile) # ignore open failure...
    tick = None
    tsindex = -1
    sampletime = 0
    inctsindex = False
    # price sums for each stock in scodes
    psums = dict()
    for s in scodes:
        psums[s] = 0.0

    for line in f:
        line = line.strip()
        if line.startswith("==="):
            # line contains time like:
            # === 2011-03-25 09:25:01.140000 ===
            t = None
            try:
                t = datetime.strptime(line, "=== %Y-%m-%d %H:%M:%S.%f ===")
            except ValueError:
                try:
                    t = datetime.strptime(line, "=== %Y-%m-%d %H:%M:%S ===")
                except ValueError:
                    pass
            # intialize tsindex to the first sample timestamp
            # which is larger than first tick
            if t is not None:
                if tick is None:
                    for i, ts in enumerate(samplets):
                        if ts >= t:
                            tsindex = i
                            break
                    if tsindex == -1:
                        # when tick is intialized to be larger than
                        # the last sample ts, and we have nothing to do.
                        break
                tick = t
            if inctsindex:
                # in the last tick the prices is sampled, and we move to
                # next sample point in time.
                tsindex += 1
                sampletime += 1
                inctsindex = False
                if tsindex >= len(samplets):
                    # last sample timestamp has been passed.
                    break
        else:
            if tick == None:
                # tick must be intialized befor sampling
                continue

            if tick >= samplets[tsindex]:
                inctsindex = True
                tmp = line.split(",")
                if tmp != []:
                    # not empty line
                    pass
                scode = tmp[0]
                sname = tmp[1]
                if scode in scodes:
                    if scode == "000300":
                        price = float(tmp[7])
                    elif scode.startswith("00"):
                        price = float(tmp[4])
                    elif scode.startswith("60"):
                        price = float(tmp[7])
                    psums[scode] += price
    f.close()

    #print 2, sampletime
    if sampletime == 0:
        return None
    else:
        pavgs = dict()
        for s in scodes:
            pavgs[s] = psums[s]/(sampletime+0.0)
        return pavgs


if __name__=="__main__":
    #sqs = glob.glob(stockqdir+os.sep+"stock*.log.gz")
    sqs = glob.glob(stockqdir+os.sep+"stock20110714.log.gz")
    sqs.sort()

    scodes = [x.strip() for x in open(scodefn)]
    df = DirectionFilter(wsize)
    for qf in sqs:
        # go through the quotes in that day for scode, and 
        # get sampled average price
        ap = sampledavg(qf, scodes)
        print ap

        #df.feed((baseap,ap))

