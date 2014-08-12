# motivation: some scp limit order is not closed immediatelly and they may 
# incur loses. Try to gather statistics on open-close intervals and trading
# profits.

import os, sys, csv

def dostat(tf):
    tstat = []
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
        if edict['event']=='set':
            tdir = -1 if 'ask' in edict else 1
            stime = edict['fts']

        elif edict['event']=='trade':
            otime = edict['fts']
            oprice = edict['price']

        elif edict['event']=='close':
            ctime = edict['fts']
            cprice = edict['price']
            earn = tdir * (cprice - oprice)

            tstat.append( [stime, otime, ctime, earn] )

            stime = 0.0
            otime = 0.0
            ctime = 0.0
            tdir = 0 # 1 for bid, -1 for ask
            oprice = 0.0
            cprice = 0.0
            earn = 0.0

    return tstat

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

    tf = open(tracefn, 'r')
    stat = dostat(tf)

    csvwrt = csv.writer(statf)
    csvwrt.writerow( ['set', 'open', 'close', 'earn'] )
    for ss in stat:
        csvwrt.writerow(ss)

    tf.close()
    statf.close()

if __name__=='__main__':
    main()

# $Id$
