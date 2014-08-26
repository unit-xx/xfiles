# read event stream generated from scplog.py and draw trading traces.

import sys, os
from datetime import datetime

def doplot(frame, plotf, fts):
    print >>plotf, 'beginframe'

    eventcnt = 0
    for ii, ff in enumerate(frame):

        if ff['event']=='quote':
            eventcnt += 1

            print >>plotf, 'quote points %d %.2f %d black' % (eventcnt, ff['bid1'], ff['bidvol1'])
            print >>plotf, 'quote points %d %.2f %d black' % (eventcnt, ff['ask1'], ff['askvol1'])

            print >>plotf, 'quote time %d NA %s' % (eventcnt, ff['time'])


        elif ff['event']=='set':
            if 'ask' in ff:
                print >>plotf, 'set points %d %.2f s red' % (eventcnt, ff['ask'])
            elif 'bid' in ff:
                print >>plotf, 'set points %d %.2f b red' % (eventcnt, ff['bid'])

        elif ff['event']=='trade':
            eventcnt += 1
            if ff['fts']==fts:
                print >>plotf, 'trade points %d %.2f T red' % (eventcnt, ff['price'])
            else:
                print >>plotf, 'trade points %d %.2f t red' % (eventcnt, ff['price'])

        elif ff['event']=='close':
            eventcnt += 1
            print >>plotf, 'close points %d %.2f c red' % (eventcnt, ff['price'])

        else:
            pass


    print >>plotf, 'endframe'

def visualone(tf, plotf, nhist):
    '''
    visualize only the last limit order which is traded
    '''

    qhist = []
    frame = []
    islazytrade = False
    isquicktrade = False

    framewithtail = []
    frametailq = []

    for line in tf:
        line = line.strip()

        event, edict = line.split(None, 1)
        try:
            edict = eval(edict)
            edict['event'] = event
        except Exception:
            pass

        if event=='quote':
            qhist.append(edict)
            frame.append(edict)

            frametodel = []
            for i in range(len(frametailq)):
                frametailq[i] += 1
                framewithtail[i].append(edict)
                if frametailq[i] == nhist:
                    # TODO: check the frame is correct.
                    doplot(framewithtail[i], plotf)

                    frametodel.append(i)

            for i in frametodel:
                del frametailq[i]
                del framewithtail[i]

        elif event=='sprdmid':
            pass

        elif event=='setlazy':
            islazytrade = False
            isquicktrade = False
            frame = []

            frame.extend(qhist[-nhist:])
            frame.append(edict)

        elif event=='asktrade':
            frame.append(edict)

        elif event=='bidtrade':
            frame.append(edict)

        elif event=='orderquick':
            frame.append(edict)

        elif event=='lazytradeinfo':
            frame.append(edict)
            islazytrade = True

            if islazytrade and isquicktrade:
                framewithtail.append(frame)
                frametailq.append(0)
                frame = []

        elif event=='quicktradeinfo':
            frame.append(edict)
            isquicktrade = True

            if islazytrade and isquicktrade:
                framewithtail.append(frame)
                frametailq.append(0)
                frame = []

        elif event=='empty':
            pass

        else:
            pass

def visualfull(tf, plotf, nhist):
    '''
    visualize every limit order until the one that is traded
    '''

    qhist = []
    frame = []
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

    for ii, edict in enumerate(fullhist):
        if edict['event']=='trade':
            fts = edict['fts']
            frame = []
            frame.extend(fullhist[max(0,ii-nhist):min(ii+nhist,len(fullhist))])
            print >>sys.stderr, max(0,ii-nhist), min(ii+nhist,len(fullhist))

            doplot(frame, plotf, fts)

def visualtime(tf, plotf, timefn):
    qhist = []
    frame = []
    fullhist = []
    tinterval = []

    # read time intervals
    timef = open(timefn)
    for line in timef:
        line = line.strip()
        starttime, endtime = line.split(None, 1)
        starttime = datetime.strptime(starttime, '%H:%M:%S').time()
        endtime = datetime.strptime(endtime, '%H:%M:%S').time()
        tinterval.append( [starttime, endtime] )
    timef.close()

    for line in tf:
        line = line.strip()

        event, edict = line.split(None, 1)
        try:
            edict = eval(edict)
            edict['event'] = event
            fullhist.append(edict)
        except Exception:
            pass

    for ttuple in tinterval:
        starttime, endtime = ttuple
        frameopen = False
        frame = []

        for ii, edict in enumerate(fullhist):
            if edict['event']=='quote':
                edicttime = datetime.strptime(edict['time'], '%H:%M:%S').time()
                if edicttime >= starttime and edicttime <= endtime:
                    frameopen = True
                else:
                    frameopen = False

            if frameopen:
                frame.append(edict)

        doplot(frame, plotf)

def main():
    mode = sys.argv[1]
    tracefn = sys.argv[2]
    if(mode=='time'):
        timefn = sys.argv[3]
    else:
        nhist = int(sys.argv[3])

    plotf = sys.stdout
    try:
        plotfn = sys.argv[4]
        if os.path.exists(plotfn):
            ans = raw_input('output file exists, overwrite? ')
            if ans!='yes':
                print >>sys.stderr, 'I quit.'
                sys.exit(1)

        plotf = open(plotfn, 'w')
    except IndexError:
        pass

    tf = open(tracefn, 'r')

    if mode=='one':
        visualone(tf, plotf, nhist)
    elif mode=='full':
        visualfull(tf, plotf, nhist)
    elif mode=='time':
        visualtime(tf, plotf, timefn)
    else:
        print 'Unknown mode, mode can be: [one, full]'

    plotf.close()
    tf.close()


if __name__=='__main__':
    main()

# $Id$
