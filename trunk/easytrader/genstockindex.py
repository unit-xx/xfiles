import sys
import pickle
from dbfpy import dbf
import ConfigParser

# read (market, code) pairs and generate scode->record mappings,
# for SH and SZ market

def genindex(stockfn, shdbfn, szdbfn):
    try:
        f = open(stockfn, "r")
    except IOError:
        print "Cannot open %s" % stockfn
        return None, None

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
            szmap["SZ"+rec["HQZQDM"]] = i
        i = i + 1
    dbsz.close()

    return shmap, szmap

def main():
    CONFIGFN = "easytrader.cfg"
    JZSEC = "jz"
    JSDSEC = "jsd"
    config = ConfigParser.RawConfigParser()
    config.read(CONFIGFN)

    print "Use setting in %s" % CONFIGFN
    print
    shmapfn = config.get(JZSEC, "shmapfn")
    szmapfn = config.get(JZSEC, "szmapfn")
    shdbfn = config.get(JZSEC, "shdbfn")
    szdbfn = config.get(JZSEC, "szdbfn")
    stockfn = config.get(JZSEC, "indexstockset")
    print "stock info dbf is %s (SH) and %s (SZ)" % (shdbfn, szdbfn)
    print "stock to be indexed is in %s" % stockfn
    print "index files are %s (SH) and %s (SZ)" % (shmapfn, szmapfn)
    print
    anwser = raw_input("Ok to continue? (y/n): ")
    if anwser.lower() != "y":
        print "You choose abort"
        sys.exit(1)

    shmap, szmap = genindex(stockfn, shdbfn, szdbfn)

    # serialize the mapping
    shmapf = open(shmapfn, "w")
    pickle.dump(shmap, shmapf)
    shmapf.close()
    szmapf = open(szmapfn, "w")
    pickle.dump(szmap, szmapf)
    szmapf.close()
    print "stock index generated."

if __name__=="__main__":
    main()
