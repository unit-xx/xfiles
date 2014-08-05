# read event stream generated from crablog.py and draw trading histories.

import sys, os
from datetime import datetime

def doplot(frame, plotf):
    print >>plotf, 'beginframe'

    eventcnt = 0
    for ii, ff in enumerate(frame):

        emptyevent = False

        if ff['event']=='quote':
            if ff['tag']=='lazy':
                print >>plotf, 'quote points %d %.2f %d black' % (eventcnt, ff['bid1'], ff['bidvol1'])
                print >>plotf, 'quote points %d %.2f %d black' % (eventcnt, ff['ask1'], ff['askvol1'])
            else:
                print >>plotf, 'quote points %d %.2f %d blue4' % (eventcnt, ff['bid1'], ff['bidvol1'])
                print >>plotf, 'quote points %d %.2f %d blue4' % (eventcnt, ff['ask1'], ff['askvol1'])

            print >>plotf, 'quote time %d NA %s' % (eventcnt, ff['time'])

        elif ff['event']=='setlazy':
            print >>plotf, 'setlazy points %d %.2f + red' % (eventcnt, ff['setlazybid'])
            print >>plotf, 'setlazy points %d %.2f + red' % (eventcnt, ff['setlazyask'])
            print >>plotf, 'setlazy text %d NA %.3f\\n%.3f\\n%.2f black' % (eventcnt, ff['sprdmid'], ff['sprdfix'], ff['delta'])

            setlazybid = ff['setlazybid']
            setlazyask = ff['setlazyask']

        elif ff['event']=='bidtrade':
            print >>plotf, 'bidtrade points %d %.2f b red' % (eventcnt, setlazybid)
            
        elif ff['event']=='asktrade':
            print >>plotf, 'asktrade points %d %.2f a red' % (eventcnt, setlazyask)

        elif ff['event']=='orderquick':
            pass

        elif ff['event']=='lazytradeinfo':
            print >>plotf, 'lazytradeinfo points %d %.2f L purple' % (eventcnt, ff['price'])

        elif ff['event']=='quicktradeinfo':
            print >>plotf, 'quicktradeinfo points %d %.2f q purple' % (eventcnt, ff['price'])

        elif ff['event']=='sprdmid':
            emptyevent = True

        else:
            emptyevent = True

        if not emptyevent:
            eventcnt += 1

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

    for ii, edict in enumerate(fullhist):
        if edict['event']=='lazytradeinfo':
            frame = []
            frame.extend(fullhist[max(0,ii-nhist):min(ii+nhist,len(fullhist))])
            print >>sys.stderr, max(0,ii-nhist), min(ii+nhist,len(fullhist))

            doplot(frame, plotf)

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