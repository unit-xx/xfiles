import sys
import pickle
from dbfpy import dbf

# read (market, code) pairs and generate scode->record mappings,
# for SH and SZ market

szmapfn = "szmap.pkl"
shmapfn = "shmap.pkl"
szdbfn = "sjshq.dbf"
shdbfn = "show2003.dbf"
stockfn = "hs300.txt"

try:
    stockfn = sys.argv[1]
except IndexError:
    print "Use"
    print "No input stock list file."
    sys.exit(1)

try:
    f = open(fn, "r")
except IOError:
    print "Cannot open %s" % fn
    sys.exit(1)

# read and make two stock lists
shlist = set()
szlist = set()
for line in f:
    tmp = line.split()
    assert len(tmp) >= 2, "Line format error."
    mkt = tmp[0]
    code = tmp[1]
    if mkt == "SH":
        shlist.add(code)
    elif mkt == "SZ":
        szlist.add(code)
f.close()

# for each list, generate the mapping
shmap = {}
szmap = {}

i = 0
dbsh = dbf.Dbf(shdbfn, ignoreErrors=True, readOnly=True)
for rec in dbsh:
    if rec["S1"] in shlist:
        shmap["SH"+rec["S1"]] = i
    i = i + 1
dbsh.close()

i = 0
dbsz = dbf.Dbf(szdbfn, ignoreErrors=True, readOnly=True)
for rec in dbsz:
    if rec["HQZQDM"] in szlist:
        print rec["HQZQDM"], i
        szmap["SH"+rec["HQZQDM"]] = i
    i = i + 1
dbsz.close()

# serialize the mapping

shmapf = open(shmapfn, "w")
pickle.dump(shmap, shmapf)
shmapf.close()
szmapf = open(szmapfn, "w")
pickle.dump(szmap, szmapf)
szmapf.close()
