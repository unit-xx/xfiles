#!/usr/bin/python

# generate batch .in/.out samples for testing.

import sys, csv, os
import ConfigParser
import sqlite3

os.putenv('NLS_LANG', 'SIMPLIFIED CHINESE_CHINA.ZHS16GBK')
import cx_Oracle

# TODO: read from config
SEC = 'main'
c = ConfigParser.ConfigParser()
c.read(sys.argv[1])
o = dict(c.items(SEC))
outdir = o['outdir']
codefn = o['codefn']
start = o['start']
end = o['end']
needex = o['needex']
market = o['market']

ip = o['ip']
port = int(o['port'])
sid = o['sid']
user = o['user']
passwd = o['passwd']

force = bool(int(o['force']))

def main():
    q1 = """
select 
    F16_1090 as code
    ,ob_object_name_1090 as name
    ,F5_1120 as open
    ,F8_1120 as close
    ,F6_1120 as high
    ,F7_1120 as low
    ,F2_1120 as "DATE"
    ,F9_1120 as vol
    ,F11_1120 as turnover
from wind.tb_object_1090,wind.TB_OBJECT_1120
where
    F16_1090=:code
    and F1_1120=F2_1090
    and F4_1090=:market
    and F5_1120 is not NULL
    and F2_1120>=:startdate
    and F2_1120<=:enddate
order by "DATE"
    """

    q2 = """
select 
    F16_1090 as code
    ,ob_object_name_1090 as name
    ,F4_1425 as open
    ,F7_1425 as close
    ,F5_1425 as high
    ,F6_1425 as low
    ,F2_1425 as "DATE"
    ,F8_1425 as vol
    ,F9_1425 as turnover
    --,F10_1425 as factor
    --,TO_CHAR(1000*F9_1425/F11_1425, 'FM9999.99') as avgprice
from wind.tb_object_1090,wind.TB_OBJECT_1425
where
    F16_1090=:code
    and F1_1425=F2_1090
    and F4_1090=:market
    and F5_1425 is not NULL
    and F2_1425>=:startdate
    and F2_1425<=:enddate
order by "DATE"
    """

    createtbl = """
CREATE TABLE IF NOT EXISTS data(
code text,
name text,
open real,
close real,
high real,
low real,
date text NOT NULL PRIMARY KEY ASC,
vol real,
turnover real
);
    """

    findexistdate = """
SELECT date FROM data
    """

    insertdata = """
INSERT OR REPLACE INTO data
VALUES (?,?,?,?,?,?,?,?,?)
    """

    if needex:
        q = q2
    else:
        q = q1

    dsn = cx_Oracle.makedsn(ip, port, sid)
    conn = cx_Oracle.connect(user, passwd, dsn)
    curs = conn.cursor()

    # security code to retrieve quotes
    scodes = []
    for x in open(codefn).readlines():
        x = x.strip()
        if x.startswith("#") or x == '':
            continue
        scodes.append(x)
    print scodes

    os.chdir(outdir)

    for code in scodes:
        print code, '...',

        # create table if not exists
        dbn = code+'.db'
        db = sqlite3.connect(dbn)
        c = db.cursor()
        c.execute(createtbl)

        # don't overwrite old data if not forced
        existdate = []
        if force == False:
            # need to find existing quotes' date
            c.execute(findexistdate)
            existdate = [x[0] for x in c.fetchall()]
        #print existdate

        # get data from wind db
        curs.execute(q, {'code':code, 'startdate':start, 'enddate':end, 'market':market})

        dateindex = 6

        # insert data
        rst = curs.fetchall()
        toinsert = []
        for r in rst:
            if r[dateindex] not in existdate:
                r = [x for x in r]
                r[1] = r[1].decode('GBK')
                toinsert.append(r)
        print '(insert %d lines out of %d results)'% (len(toinsert), len(rst)),
        c.executemany(insertdata, toinsert)

        db.commit()
        db.close()

        print 'done'

    conn.close()

if __name__=="__main__":
    main()

