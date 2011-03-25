import time
import datetime
import gzip

from dbfpy import dbf
from genstockindex import genindex

logfn = ""
logf = None
shdbfn = "z:\show2003.dbf"
szdbfn = "z:\sjshq.dbf"
indexstockset = "hs300.txt"

starttime = datetime.time(9, 25, 00)
endtime = datetime.time(15, 05, 00)
recstate = 0
shmap = {}
szmap = {}

try:
    while 1:
        time.sleep(5)

        now = datetime.datetime.now()
        nowtime = datetime.datetime.now().time()

        if nowtime > starttime and nowtime < endtime:
            # start a new record period.
            if recstate == 0:
                print now, "generating index for a new day!"
                shmap, szmap = genindex(indexstockset,
                        shdbfn,
                        szdbfn)
                if shmap is None or szmap is None:
                    print "gen stock map failed."

                print now, "gen new log file name."
                logfn = "stock%4d%02d%02d.log" % (now.year, now.month, now.day)
                logfnz = logfn+".gz"
                logf = open(logfn, "a")
                logfz = gzip.open(logfnz, "a")

                dbsh = dbf.Dbf(shdbfn, ignoreErrors=True, readOnly=True)
                dbsz = dbf.Dbf(szdbfn, ignoreErrors=True, readOnly=True)

            recstate = 1 # 1 for open
        else:
            recstate = 0 # 0 for close
            if logf is not None:
                print now, "close logs."
                logf.close()
                logfz.close()
                logf = None
                logfz = None
                logfn = ""
                logfnz = ""
                dbsh.close()
                dbsz.close()

        if recstate:
            print >>logf, '===',now,'==='
            print >>logfz, '===',now,'==='
            for scode in shmap:
                rec = dbsh[shmap[scode]]
                recstr = ",".join([str(x) for x in rec])
                print >>logf, recstr
                print >>logfz, recstr

            for scode in szmap:
                rec = dbsz[szmap[scode]]
                recstr = ",".join([str(x) for x in rec])
                print >>logf, recstr
                print >>logfz, recstr

            logf.flush()
            logfz.flush()
except KeyboardInterrupt:
    print "going to exit"
    if logf is not None:
        logf.close()
        logfz.close()
        logf = None
        logfz - None
        logfn = ""
        logfnz = ""
        dbsh.close()
        dbsz.close()
