# extract quote, order and trade log from scpstrat's log and write to a file.

import sys, os
from datetime import datetime

def main():
    logfn = sys.argv[1]
    logtracefn = sys.argv[2]
    if(os.path.exists(logtracefn)):
        isow = raw_input('trace file exists, overwrite? ')
        if isow!='yes':
            print 'No action taken, I exit.'
            sys.exit(1)

    tf = open(logtracefn, 'w')

    for line in open(logfn):
        line = line.strip()
        loglet = line.split('&')
        loglet = [x.strip() for x in loglet]
        '''
        loglet looks like this now:

        ['2014-05-30 10:34:10,825', 'INFO', 'crab.py', 'signal', 'L:143', 'P:1072', 'T:crabstrat', 'TID:7200', 'new quick quote code IF1406 ask1 2151.80 askvol1 55 bid1 2151.40 bidvol1 55 time 10:31:22 msec 0 tic 37882.00']
        '''
        event = None
        edict = {}
        # calc timestamp in float numbers
        ts = datetime.strptime(loglet[0], '%Y-%m-%d %H:%M:%S,%f')
        fts = ts.hour*3600 + ts.minute*60 + ts.second + ts.microsecond/1000000.0
        edict['fts'] = fts
        edict['ts'] = loglet[0]

        if loglet[-1].startswith('new quick quote'):
            event = 'quote'
            edict['tag'] = 'quick'
            tmp = loglet[-1].split(None,3)[-1].split()
            keys = tmp[0:len(tmp):2]
            values = tmp[1:len(tmp):2]

            values[1] = float(values[1])
            values[3] = float(values[3])
            values[7] = float(values[7])

            values[2] = int(values[2])
            values[4] = int(values[4])
            values[6] = int(values[6])

            edict.update(zip(keys, values))

        elif loglet[-1].startswith('setting'):
            event = 'set'

            tmp = loglet[-1].split()[1:]
            tmp = [x.strip(',') for x in tmp]
            keys = []
            values = []
            for kv in tmp:
                if '=' in kv:
                    k,v = kv.split('=')
                    keys.append(k)
                    values.append(v)

            for i in range(len(values)):
                try:
                    values[i] = float(values[i])
                except:
                    pass

            edict.update(zip(keys, values))

        elif loglet[-1].startswith('limit order traded'):
            event = 'trade'

            tmp = loglet[-1].split()[3:]
            keys = []
            values = []
            for kv in tmp:
                k,v = kv.split('=')
                keys.append(k)
                values.append(v)

            for i in range(len(values)):
                try:
                    values[i] = float(values[i])
                except:
                    pass
            
            edict.update(zip(keys, values))

        elif loglet[-1].startswith('close order traded'):
            event = 'close'

            tmp = loglet[-1].split()[3:]
            keys = []
            values = []
            for kv in tmp:
                k,v = kv.split('=')
                keys.append(k)
                values.append(v)

            for i in range(len(values)):
                try:
                    values[i] = float(values[i])
                except:
                    pass
            
            edict.update(zip(keys, values))

        else:
            # un-processed line
            event = 'empty'
            edict = line

        print >>tf, event, str(edict)

    tf.close()

if __name__=='__main__':
    main()
# $Id$
