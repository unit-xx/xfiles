# data genrated by scpstat.py is very basic. scpstat2 tries to find
# some `correlations' between trading profits and varies properties
# such as bid/ask volumes, price trend, etc.

import os, sys, csv

def dostat(tf, qnum):
    # trend3, trend5
    # b/a spread 3/5 -> max and avg
    # volumes 3/5 -> diff, ratio, ...
    tstat = []
    colnames = ['set', 'open', 'close', 'tdir', 'earn', 'oprice', 'cprice']

    for line in tf:
        line = line.strip()

    stime = 0.0
    otime = 0.0
    ctime = 0.0
    tdir = 0 # 1 for bid, -1 for ask
    oprice = 0.0
    cprice = 0.0
    earn = 0.0


    return tstat

def main():
    statfn = sys.argv[1]
    try:
        stat2fn = sys.argv[2]
        if os.path.exists(statfn):
            ans = raw_input('output file exists, overwrite? ')
            if ans!='yes':
                print >>sys.stderr, 'I quit.'
                sys.exit(1)

        stat2f = open(statfn, 'w')
    except IndexError:
        stat2f = sys.stdout

    qnum = 10
    try:
        qnum = int(sys.argv[3])
    except:
        pass

    statf = open(statfn, 'r')
    colnames, stat2 = dostat2(tf, qnum)

    csvwrt = csv.writer(stat2f)
    csvwrt.writerow(colnames)
    for ss in stat2:
        csvwrt.writerow(ss)

    statf.close()
    stat2f.close()

if __name__=='__main__':
    main()

# $Id$
