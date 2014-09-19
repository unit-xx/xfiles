# some ask2/bid2 trades cannot be closed immediately. What if we follow the trend by buying/selling the contract.

import os, sys, csv

def dotrend(tf, qnum):
    fullhist = []

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

    # summary of trade set/open/close time and trade postion in fullhist
    tradesummary = []
    tradepos = []
    trendsum = []
    seequote = 0

    stime = 0.0
    otime = 0.0
    ctime = 0.0
    tdir = 0 # 1 for bid, -1 for ask
    oprice = 0.0
    cprice = 0.0
    earn = 0.0

    for ii, edict in enumerate(fullhist):

        # last set operation
        if edict['event']=='set':
            tdir = -1 if 'ask' in edict else 1
            stime = edict['fts']

        # last open trade
        elif edict['event']=='trade':
            otime = edict['fts']
            oprice = edict['price']
            seequote = 0
            tradepos.append(ii)

        # record a trading `frame' when position is closed.
        elif edict['event']=='close':
            ctime = edict['fts']
            cprice = edict['price']
            earn = (cprice-oprice)*tdir

            row = [stime, otime, ctime, tdir, earn, oprice, cprice, seequote]
            trendsum.append(row)

        elif edict['event']=='quote':
            seequote = 1

    # now we go through each trading and see how the trend goes.
    histlen = len(fullhist)
    for ii, pos in enumerate(tradepos):
        ts = trendsum[ii]
        kk = pos + 1
        qhist = []

        while 1:

            if kk >= histlen:
                break

            if fullhist[kk]['event']=='quote':
                qhist.append(fullhist[kk]['ask1'])
                qhist.append(fullhist[kk]['bid1'])

            kk += 1

            if len(qhist) >= 2*qnum:
                break

        ts.extend(qhist)

    return trendsum

def main():
    tracefn = sys.argv[1]
    try:
        trendfn = sys.argv[2]
        if os.path.exists(trendfn):
            ans = raw_input('output file exists, overwrite? ')
            if ans!='yes':
                print >>sys.stderr, 'I quit.'
                sys.exit(1)

        trendf = open(trendfn, 'w')
    except IndexError:
        trendf = sys.stdout

    qnum = 100
    try:
        qnum = int(sys.argv[3])
    except:
        pass

    tf = open(tracefn, 'r')
    trendsum = dotrend(tf, qnum)

    csvwrt = csv.writer(trendf)
    csvwrt.writerows(trendsum)

    tf.close()

if __name__=='__main__':
    main()

# $Id$
