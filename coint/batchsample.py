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

ip = o['ip']
port = int(o['port'])
sid = o['sid']
user = o['user']
passwd = o['passwd']

force = bool(int(o['force']))

def main():
    q = """
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
    and F4_1090='S'
    and F5_1120 is not NULL
    --and rownum <=2
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

    dsn = cx_Oracle.makedsn(ip, port, sid)
    conn = cx_Oracle.connect(user, passwd, dsn)
    curs = conn.cursor()

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

        existdate = []
        if force == False:
            # need to find existing quotes' date
            c.execute(findexistdate)
            existdate = [x[0] for x in c.fetchall()]
        #print existdate

        # get data from wind db
        curs.execute(q, {'code':code})

        dateindex = 6

        rst = curs.fetchall()
        toinsert = []
        for r in rst:
            if r[dateindex] not in existdate:
                r = [x for x in r]
                r[1] = r[1].decode('GBK')
                toinsert.append(r)
        print '(insert %d lines)'%len(toinsert) ,
        c.executemany(insertdata, toinsert)

        db.commit()
        db.close()

        print 'done'

    conn.close()

if __name__=="__main__":
    main()

