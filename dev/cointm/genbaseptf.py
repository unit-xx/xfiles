# generate base portfolio for 1vN strategies. The base portfolio here is the buying leg, and the short leg is 000300 so far.

import sys, csv, os
import ConfigParser
import sqlite3
from collections import defaultdict

os.putenv('NLS_LANG', 'SIMPLIFIED CHINESE_CHINA.ZHS16GBK')
import cx_Oracle

c_multiplier=300
c_shares=5
c_cointdbn='hs300index.db'
c_betafrom='large3'
c_quotedbdir='hs300indexout'
c_visuallist="select '000300.000908.000915.000917' as cpair"

c_ip = '172.18.19.37'
c_port = 1521
c_sid = 'webdb1'
c_user = 'beijing'
c_passwd = 'beijing'

#c_visuallist="select cpair from large3 where pvalue < 0.05 AND hlife < 25"

# read beta of buying leg, and read weight from wind db.

betaq = 'select cpair, beta from %s where cpair=?' % c_betafrom

lastdateq = "select max(F2_1120) from wind.tb_object_1090,wind.TB_OBJECT_1120 where F16_1090='000300' and F1_1120=F2_1090 and F4_1090='S'"

quoteq1 = 'select F8_1120 from wind.tb_object_1090,wind.TB_OBJECT_1120 where F1_1120=F2_1090 and F16_1090=:code and F4_1090=:mkt and F2_1120=:day'

weightq = ''

stkalloc = defaultdict(float)

cointdb = sqlite3.connect(c_cointdbn)
cpairs = [x[0] for x in cointdb.execute(c_visuallist).fetchall()]

dsn = cx_Oracle.makedsn(c_ip, c_port, c_sid)
conn = cx_Oracle.connect(c_user, c_passwd, dsn)
curs = conn.cursor()

for bleg in cpairs:
    # read beta for buy legs
    legcode, beta = cointdb.execute(betaq, (bleg,)).fetchall()[0]
    legs = legcode.split('.')[1:]
    beta = [float(x) for x in beta.split(';')]

    lastday = curs.execute(lastdateq).fetchall()[0][0]

    # read weight for comonents for buy lesg
    # NOTE: wind db error, and read from file temporarily.
    # read latest quotes for buy legs
    for i, l in enumerate(legs):
        legq = curs.execute(quoteq1, {'code':l, 'mkt':'S', 'day':lastday}).fetchall()[0][0]
        wtfn = l+'.wt'
        for line in open(os.path.join(c_quotedbdir, wtfn)):
            stk, weight = line.split()
            stkalloc[stk] += legq * beta[i] * float(weight) * c_multiplier * c_shares/100
    # now we have capital allocation for each component stock.
    # and we can read the latest close prices and generate the portfolio in stock count

    print 'IF,IF,%d'%c_shares
    for s in stkalloc:
        sq = curs.execute(quoteq1, {'code':s, 'mkt':'A', 'day':lastday}).fetchall()[0][0]
        stkalloc[s] = stkalloc[s]/sq
        mkt = ''
        if s[0:4] == '000':
            mkt = 'SZ'
        else:
            mkt = 'SH'
        print ','.join([mkt, s, str(int(stkalloc[s]))])





