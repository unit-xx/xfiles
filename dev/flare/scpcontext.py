# set limit price at ask2/bid2, when the order is hit, close it at ask1/bid1.
# if the order is not closed immediately (within 2 seconds, typically), it is 
# closed using market order, and a long/short order is opened because we think
# there's a strong bull/bear run in short term.

# collecting traces, under the conditions of vol>xxx, volratio>yyy.
# trace length is not fixed. two output files are written. first is a 
# quote trace file with <tick, price, vol, ...>, and the second is 
# trace file which record trading ticks.

import os, sys, csv

def docontext(tf):
    # TODO: trim quotes not in today
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

    qhist = []
    thist = []
    lastqtick = -1
    qattr = ['tic', 'ask1', 'askvol1', 'bid1', 'bidvol1']
    tattr = ['stime', 'otime', 'ctime', 'tdir', 'earn', 'oprice', 'cprice', 'seequote', 'force']
    qhist.append(qattr)
    thist.append(tattr)

    stime = 0.0
    otime = 0.0
    ctime = 0.0
    tdir = 0 # 1 for bid, -1 for ask
    earn = 0.0
    oprice = 0.0
    cprice = 0.0
    seequote = 0
    isforce = 0

    for ii, edict in enumerate(fullhist):
        if edict['event']=='quote':
            qhist.append([edict[x] for x in qattr])
            lastqtick = edict['tic']
            seequote = 1

        elif edict['event']=='set':
            tdir = -1 if 'ask' in edict else 1
            stime = lastqtick

        elif edict['event']=='trade':
            otime = lastqtick
            oprice = edict['price']
            seequote = 0

        elif edict['event']=='close':
            ctime = lastqtick
            cprice = edict['price']
            earn = (cprice-oprice)*tdir
            isforce = 1 if (('force' in edict) and (edict['force']=='yes')) else 0

            row = [stime, otime, ctime, tdir, earn, oprice, cprice, seequote, isforce]
            thist.append(row)

    return qhist, thist

def main():
    tracefn = sys.argv[1]
    try:
        quotefn = sys.argv[2]
        tradefn = sys.argv[3]
        if os.path.exists(quotefn) or os.path.exists(tradefn):
            ans = raw_input('output file exists, overwrite? ')
            if ans!='yes':
                print >>sys.stderr, 'I quit.'
                sys.exit(1)

        quotef = open(quotefn, 'w')
        tradef = open(tradefn, 'w')
    except IndexError:
        print >>sys.stderr, 'No output filename specified, I quit.'
        sys.exit(1)

    tracef = open(tracefn, 'r')
    quotehist, tradehist = docontext(tracef)

    csvwrt1 = csv.writer(quotef)
    csvwrt1.writerows(quotehist)
    csvwrt2 = csv.writer(tradef)
    csvwrt2.writerows(tradehist)

    tracef.close()
    quotef.close()
    tradef.close()

if __name__=='__main__':
    main()

# $Id$
