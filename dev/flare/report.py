# report orders to a csv file
# usage: report.py strat <reportfn>, reportfn default to strat.<day>.csv

import sys, os
import csv
from datetime import date, datetime

from flamelib import TBookLib, getstore
import flaredef as fdef
import config

def main(args):
    mysec = 'report'
    cfg = config.parseconfig()
    mycfg = cfg[mysec]

    storecfg = cfg[mycfg['store']]
    storecfg['port'] = int(storecfg['port'])
    storecfg['db'] = int(storecfg['db'])

    store = getstore(storecfg)
    if store is None:
        raise Exception('connecting to store failed.')

    try:
        strat = args[1]
    except IndexError:
        print 'Usage: strat (reportfn), reportfn default to strat.<day>.csv'
        raise Exception('Not enough arguments.')

    try:
        rptfn = args[2]
    except IndexError:
        todaystr = date.today().strftime('%Y%m%d')
        rptfn = '.'.join((strat, todaystr, 'csv'))

    print rptfn

    rptfieldraw = mycfg['rptfield'].split()
    rptfield = []
    for fd in rptfieldraw:
        try:
            fdtrans = getattr(fdef, fd)
        except AttributeError:
            fdtrans = fd
        rptfield.append(fdtrans)

    print rptfield

    tb2strat = store.hgetall(fdef.TB2STRATMAP)
    strat2tb = {tb2strat[k]:k for k in tb2strat}

    tbname = strat2tb[strat]
    tblib = TBookLib(store, tbname)
    alloids = tblib.getalloid()
    neworders = []
    for oid in alloids:
        neworders.append(tblib.getorder(oid))
    neworders.sort(key=lambda x: datetime.strptime(x[fdef.KORDERDATE], config.GCONFIG['dateformat']))

    for o in neworders:
        print o
        print

if __name__=="__main__":
    main(sys.argv)

# $Id$
