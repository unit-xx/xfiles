# motivation: some scp limit order is not closed immediatelly and they may 
# incur loses. Try to gather statistics on open-close intervals and trading
# profits.

import os, sys, csv

def dostat(tf, qnum):
    tstat = []
    fullhist = []

    colnames = ['set', 'open', 'close', 'tdir', 'earn', 'oprice', 'cprice']
    for i in range(1, 11, 1):
        j = str(i)
        tmp = ['ask'+j, 'askvol'+j, 'bid'+j, 'bidvol'+j]
        colnames.extend(tmp)

    for line in tf:
        line = line.strip()

        event, edict = line.split(None, 1)
        try:
            edict = eval(edict)
            edict['event'] = event
            fullhist.append(edict)
        except Exception:
            pass

    # a dirty hack for logging bug in scp.py: forced closing 
    # 'close' was mis-logged as 'trade'
    isopen = False
    for ii, edict in enumerate(fullhist):
        if edict['event']=='trade' and isopen:
            edict['event'] = 'close'

        if edict['event']=='trade' or edict['event']=='close':
            isopen = not isopen

    stime = 0.0
    otime = 0.0
    ctime = 0.0
    tdir = 0 # 1 for bid, -1 for ask
    oprice = 0.0
    cprice = 0.0
    earn = 0.0

    state = 'close'
    # flow: set -> trade -> close
    for ii, edict in enumerate(fullhist):

        # last set operation
        if edict['event']=='set':
            tdir = -1 if 'ask' in edict else 1
            stime = edict['fts']

        # last open trade
        elif edict['event']=='trade':
            otime = edict['fts']
            oprice = edict['price']

        # record a trading `frame' when position is closed.
        elif edict['event']=='close':
            ctime = edict['fts']
            cprice = edict['price']
            earn = tdir * (cprice - oprice)

            row = [stime, otime, ctime, tdir, earn, oprice, cprice, ]

            # going back for last 10 quotes

            kk = ii - 1
            nq = 0

            # first go back to trade point
            while 1:
                if kk < 0:
                    break

                if fullhist[kk]['event']=='trade':
                    break

                kk -= 1

            # then record last qnum quotes
            while 1:
                if kk < 0:
                    break

                if fullhist[kk]['event']=='quote':
                    qinfo = [fullhist[kk][x] for x in ('ask1', 'askvol1', 'bid1', 'bidvol1')]
                    row.extend(qinfo)
                    nq += 1

                if nq >= qnum:
                    break

                kk -= 1

            tstat.append(row)

            stime = 0.0
            otime = 0.0
            ctime = 0.0
            tdir = 0 # 1 for bid, -1 for ask
            earn = 0.0
            oprice = 0.0
            cprice = 0.0

    return tstat, colnames

def main():
    tracefn = sys.argv[1]
    try:
        statfn = sys.argv[2]
        if os.path.exists(statfn):
            ans = raw_input('output file exists, overwrite? ')
            if ans!='yes':
                print >>sys.stderr, 'I quit.'
                sys.exit(1)

        statf = open(statfn, 'w')
    except IndexError:
        statf = sys.stdout

    qnum = 10
    try:
        qnum = int(sys.argv[3])
    except:
        pass

    tf = open(tracefn, 'r')
    stat, colnames = dostat(tf, qnum)

    csvwrt = csv.writer(statf)
    csvwrt.writerow(colnames)
    for ss in stat:
        csvwrt.writerow(ss)

    tf.close()
    statf.close()

if __name__=='__main__':
    main()

# $Id$
