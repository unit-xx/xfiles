#!/usr/bin/python

# generate batch .in/.out samples for testing.
# use gangao db

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
isindex = int(o['isindex'])
isfund = int(o['isfund'])

ip = o['ip']
port = int(o['port'])
sid = o['sid']
user = o['user']
passwd = o['passwd']

force = bool(int(o['force']))

def main():
    qstk = """
select
    b.tradingcode as code, 
    b.secuabbr as name, 
    a.openingprice as open, 
    a.closingprice as close, 
    a.highestprice as high, 
    a.lowestprice as low, 
    --a.adjustclosingprice as adjclose, 
    TO_CHAR(a.tradingday, 'yyyymmdd') as "DATE", 
    a.turnovervol as vol, 
    a.turnoverval as turnover, 
    a.adjustclosingprice/a.closingprice as factor
from center_admin.stk_dailyquote a, center_admin.stk_basicinfo b 
where 
    b.tradingcode=:code 
    and a.secucode=b.secucode 
    and a.tradingstate=1
    and a.tradingday>=TO_DATE(:startdate, 'yyyymmdd')
    and a.tradingday<=TO_DATE(:enddate, 'yyyymmdd')
    """

    qinx = """
select
    b.tradingcode as code, 
    b.secuabbr as name, 
    a.openingprice as open, 
    a.closingprice as close, 
    a.highestprice as high, 
    a.lowestprice as low, 
    --a.closingprice as adjclose, 
    TO_CHAR(a.tradingday, 'yyyymmdd') as "DATE", 
    a.turnovervol as vol, 
    a.turnoverval as turnover, 
    1 as factor
from center_admin.inx_dailyquote a, center_admin.inx_basicinfo b 
where 
    b.tradingcode=:code
    and a.indexcode=b.secucode 
    and a.tradingstate=1
    and a.tradingday>=TO_DATE(:startdate, 'yyyymmdd')
    and a.tradingday<=TO_DATE(:enddate, 'yyyymmdd')
    """

    qfund = """
select
    b.tradingcode as code, 
    b.secuabbr as name, 
    a.openingprice as open, 
    a.closingprice as close, 
    a.highestprice as high, 
    a.lowestprice as low, 
    TO_CHAR(a.tradingday, 'yyyymmdd') as "DATE", 
    a.turnovervol as vol, 
    a.turnoverval as turnover, 
    a.adjustclosingprice/a.closingprice as factor
from center_admin.fnd_dailyquote a, center_admin.fnd_basicinfo b 
where 
    b.tradingcode=:code
    and a.secucode=b.secucode 
    and a.tradingstate=1
    and a.tradingday>=TO_DATE(:startdate, 'yyyymmdd')
    and a.tradingday<=TO_DATE(:enddate, 'yyyymmdd')
    """

    createtbl = """
CREATE TABLE IF NOT EXISTS data(
code text,
name text,
open real,
close real,
high real,
low real,
--adjclose real,
date text NOT NULL PRIMARY KEY ASC,
vol real,
turnover real,
factor real
);
    """

    findexistdate = """
SELECT date FROM data
    """

    insertdata = """
INSERT OR REPLACE INTO data
VALUES (?,?,?,?,?,?,?,?,?,?)
    """

    if isindex:
        q = qinx
        print 1
    elif isfund:
        q = qfund
        print 2
    else:
        q = qstk

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
        curs.execute(q, {'code':code, 'startdate':start, 'enddate':end})

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

