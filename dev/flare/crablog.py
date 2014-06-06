# extract quote, order and trade log from crabstrat's log and write to a file.

import sys, os

def main():
    logfn = sys.argv[1]
    logtracefn = sys.argv[2]
    if(os.path.exist(logtracefn)):
        isow = raw_input('trace file exists, overwrite? ')
        if isow!='yes':
            print 'No action taken, I exit.'
            sys.exit(1)

    for line in open(logfn):
        loglet = line.split('&')
        loglet = [x.strip() for x in loglet]
        '''
        loglet looks like this now:

        ['2014-05-30 10:34:10,825', 'INFO', 'crab.py', 'signal', 'L:143', 'P:1072', 'T:crabstrat', 'TID:7200', 'new quick quote code IF1406 ask1 2151.80 askvol1 55 bid1 2151.40 bidvol1 55 time 10:31:22 msec 0 tic 37882.00']
        '''
        outline = []
        if loglet[-1].startswith('new quick quote code'):
            outline.append('quote')
            outline.append('quick')
            outline.append(loglet[-1].split(None,4)[-1])
        elif loglet[-1].startswith('new lazy quote code'):
            outline.append('quote')
            outline.append('lazy')
            outline.append(loglet[-1].split(None,4)[-1])
        elif loglet[-1].startswith('new sprdmid'):
            outline.append('quote mid')
            outline.append(loglet[-1].split()[2])
        elif loglet[-1].startswith('set lazy limit'):
            x
        elif loglet[-1].startswith('ask traded'):
            x
        elif loglet[-1].startswith('bid traded'):
            x
        elif loglet[-1].startswith('order quick at fully trade'):
            x
        elif loglet[-1].startswith('lazy traded with'):
            x
        elif loglet[-1].startswith('quick traded with'):
            x
        else:
            # un-processed line
            print loglet

# $Id$
