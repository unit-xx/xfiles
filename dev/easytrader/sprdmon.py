# read stock configurations and monitor its spread

import sys
import time, datetime

from dbfpy import dbf
from genstockindex import genindex

shdbfn = 'z:\\show2003.dbf'
szdbfn = 'z:\\sjshq.dbf'
sprddeffn = sys.argv[1]
sprdoutfn = sprddeffn.split()[0]+'.rec'
sprdoutf = open(sprdoutfn, 'a')
sprdcfg = {}
pricerec = {}

for line in open(sprddeffn):
    tmp = line.split()
    code = tmp[0] + tmp[1]
    count = float(tmp[2])
    sprdcfg[code] = count
    pricerec[code] = 0.0

shmap, szmap = genindex(sprddeffn, shdbfn, szdbfn)

dbsh = dbf.Dbf(shdbfn, ignoreErrors=True, readOnly=True)
dbsz = dbf.Dbf(szdbfn, ignoreErrors=True, readOnly=True)

while 1:
    for c in sprdcfg:
        p = 0.0
        if c[0:2] == 'SH':
            p = float(dbsh[shmap[c]]['S8'])
        elif c[0:2] == 'SZ':
            p = float(dbsz[szmap[c]]['HQZJCJ'])
        pricerec[c] = p

    sprd = 0.0
    for c in pricerec:
        sprd += pricerec[c] * sprdcfg[c]

    print str(datetime.datetime.now()), "%.2f"%sprd
    print >>sprdoutf, str(datetime.datetime.now()), "%.2f"%sprd
    sprdoutf.flush()

    time.sleep(5)
