# read event stream generated from crablog.py and draw trading histories.

import sys, os

def doplot(frame):
    print 'beginframe'
    for ii, ff in enumerate(frame):
        if ff['event']=='quote':
            if ff['tag']=='lazy':
                print 'quote points %d %.2f - black' % (ii, ff['bid1'])
                print 'quote points %d %.2f - black' % (ii, ff['ask1'])
            else:
                print 'quote points %d %.2f - black' % (ii, ff['bid1'])
                print 'quote points %d %.2f - black' % (ii, ff['ask1'])

        elif ff['event']=='setlazy':
            print 'setlazy points %d %.2f + red' % (ii, ff['setlazybid'])
            print 'setlazy points %d %.2f + red' % (ii, ff['setlazyask'])

            setlazybid = ff['setlazybid']
            setlazyask = ff['setlazyask']

        elif ff['event']=='bidtrade':
            print 'bidtrade points %d %.2f b red' % (ii, setlazybid)
            
        elif ff['event']=='asktrade':
            print 'asktrade points %d %.2f a red' % (ii, setlazyask)

        elif ff['event']=='orderquick':
            pass

        elif ff['event']=='lazytradeinfo':
            print 'lazytradeinfo points %d %.2f L purple' % (ii, ff['price'])

        elif ff['event']=='quicktradeinfo':
            print 'quicktradeinfo points %d %.2f q purple' % (ii, ff['price'])
    print 'endframe'

def main():
    tracefn = sys.argv[1]
    nhist = int(sys.argv[2])

    tf = open(tracefn, 'r')

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

            print len(frametailq), 't'
            for i in range(len(frametailq)):
                print len(frametailq)
                print(range(len(frametailq)))
                print i
                print(len(framewithtail))
                print(frametailq)
                frametailq[i] += 1
                framewithtail[i].append(edict)
                if frametailq[i] == nhist:
                    # TODO: check the frame is correct.
                    #doplot(framewithtail[i])

                    del framewithtail[i]
                    del frametailq[i]

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

if __name__=='__main__':
    main()

# $Id$
