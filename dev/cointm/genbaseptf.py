# generate base portfolio for 1vN strategies. The base portfolio here is the buying leg, and the short leg is 000300 so far.

import sys, csv, os
import ConfigParser
import datetime
import sqlite3
from collections import defaultdict

os.putenv('NLS_LANG', 'SIMPLIFIED CHINESE_CHINA.ZHS16GBK')
import cx_Oracle

c_multiplier=300
c_shares=5
c_cointdbn='hs300index.db'
c_betafrom='large3'
c_quotedbdir='hs300indexout'
c_visuallist="select '000300.000908.000911.000917' as cpair"

c_ip = '172.18.18.67'
c_port = 1521
c_sid = 'centerdb'
c_user = 'center_read'
c_passwd = 'center_read'

#c_visuallist="select cpair from large3 where pvalue < 0.05 AND hlife < 25"

# read beta of buying leg, and read weight from wind db.

betaq = 'select cpair, beta from %s where cpair=?' % c_betafrom

lastdateq = "select TO_CHAR(max(a.tradingday), 'yyyymmdd') from center_admin.inx_dailyquote a, center_admin.inx_basicinfo b where b.tradingcode='000300' and a.indexcode=b.secucode"

quoteinx = "select closingprice from center_admin.inx_dailyquote a, center_admin.inx_basicinfo b where b.tradingcode=:code and a.indexcode=b.secucode and tradingday=TO_DATE(:day,'yyyymmdd')"

quotestk = "select closingprice from center_admin.stk_dailyquote a, center_admin.stk_basicinfo b where b.tradingcode=:code and a.secucode=b.secucode and tradingday=TO_DATE(:day,'yyyymmdd')"

weightq = ''

stkalloc = defaultdict(float)

cointdb = sqlite3.connect(c_cointdbn)
cpairs = [x[0] for x in cointdb.execute(c_visuallist).fetchall()]

dsn = cx_Oracle.makedsn(c_ip, c_port, c_sid)
conn = cx_Oracle.connect(c_user, c_passwd, dsn)
curs = conn.cursor()

legcap = 0.0
for pair in cpairs:
    # read beta for buy legs
    legcode, beta = cointdb.execute(betaq, (pair,)).fetchall()[0]
    legs = legcode.split('.')[1:]
    beta = [float(x) for x in beta.split(';')]

    lastday = curs.execute(lastdateq).fetchall()[0][0]

    # read weight for components for buy lesg
    # read latest quotes for buy legs
    for i, l in enumerate(legs):
        legq = curs.execute(quoteinx, {'code':l, 'day':lastday}).fetchall()[0][0]
        legcap += legq * beta[i] * c_multiplier * c_shares
        wtfn = l+'.wt'
        wtf = open(os.path.join(c_quotedbdir, wtfn), 'rb')
        csvrd = csv.reader(wtf)
        for line in csvrd:
            stk, weight = line
            stkalloc[stk] += legq * beta[i] * float(weight) * c_multiplier * c_shares/100
        wtf.close()
    stkcap = sum(stkalloc.values())
    print "stkcap: %.3f, legcap: %.3f, diffratio: %.3f%%" % (stkcap, legcap, 100*(stkcap-legcap)/legcap)

    # now we have capital allocation for each component stock.
    # and we can read the latest close prices and generate the portfolio in stock count
    today = (datetime.datetime.today().strftime('%Y%m%d'))
    ptf = open('.'.join([pair, today, 'ptf']), 'wb')
    csvwrt = csv.writer(ptf)
    csvwrt.writerow(['IF', 'IF', c_shares])
    for s in stkalloc:
        sq = curs.execute(quotestk, {'code':s, 'day':lastday}).fetchall()[0][0]
        stkalloc[s] = stkalloc[s]/sq
        mkt = ''
        if s[0:2] == '00':
            mkt = 'SZ'
        else:
            mkt = 'SH'
        csvwrt.writerow([mkt, s, str(int(stkalloc[s]))])
    ptf.close()

    legcap = 0.0

