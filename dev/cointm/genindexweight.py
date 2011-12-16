import sys, csv, os
import ConfigParser
import sqlite3
from collections import defaultdict

os.putenv('NLS_LANG', 'SIMPLIFIED CHINESE_CHINA.ZHS16GBK')
import cx_Oracle

c_quotedbdir='hs300indexout'
c_codefn='hs300indexa'

c_ip = '172.18.18.67'
c_port = 1521
c_sid = 'centerdb'
c_user = 'center_read'
c_passwd = 'center_read'

stklastdateq = "select TO_CHAR(max(a.tradingday), 'yyyymmdd') from center_admin.stk_dailyquote a, center_admin.stk_basicinfo b where b.tradingcode=:code and a.secucode=b.secucode"

wtlastdateq = "select TO_CHAR(max(a.tradingday), 'yyyymmdd') from center_admin.inx_componentweight a, center_admin.inx_basicinfo b where b.tradingcode=:code and a.indexcode=b.secucode"

wtq = "select c.tradingcode, b.tradingcode, weight, tradingday from center_admin.inx_componentweight a, center_admin.inx_basicinfo b, center_admin.stk_basicinfo c where a.indexcode=b.secucode and a.secucode=c.secucode and b.tradingcode=:code and a.tradingday=TO_DATE(:day,'yyyymmdd')"

quoteinx = "select closingprice from center_admin.inx_dailyquote a, center_admin.inx_basicinfo b where b.tradingcode=:code and a.indexcode=b.secucode and tradingday=TO_DATE(:day,'yyyymmdd')"

quotestk = "select closingprice from center_admin.stk_dailyquote a, center_admin.stk_basicinfo b where b.tradingcode=:code and a.secucode=b.secucode and tradingday=TO_DATE(:day,'yyyymmdd')"

dsn = cx_Oracle.makedsn(c_ip, c_port, c_sid)
conn = cx_Oracle.connect(c_user, c_passwd, dsn)
curs = conn.cursor()

wt = {}
cwt = {}
for line in open(c_codefn):
    index = line.strip()
    if (len(index)==0 or index.startswith('#')):
        continue

    # get weight first
    wtday = curs.execute(wtlastdateq, {'code':index}).fetchall()[0][0]
    wtrst = curs.execute(wtq, {'code':index, 'day':wtday})
    for r in wtrst:
        code = r[0]
        weight = r[2]
        wt[code]=weight

    # then check its accuracy
    # step 1: calculate stock numbers
    indexquote = float(curs.execute(quoteinx, {'code':index, 'day':wtday}).fetchall()[0][0])
    for c in wt:
        stkquote = float(curs.execute(quotestk, {'code':c, 'day':wtday}).fetchall()[0][0])
        cwt[c] = indexquote * wt[c]/100.0/stkquote

    # step 1: calcuate index quote according to stock count weight and quote in the last day of stock quote 
    indexquote2 = 0.0
    stkday = curs.execute(stklastdateq, {'code':wt.keys()[0]}).fetchall()[0][0]
    for c in cwt:
        stkquote = float(curs.execute(quotestk, {'code':c, 'day':stkday}).fetchall()[0][0])
        indexquote2 += cwt[c] * stkquote
    indexquote3 = float(curs.execute(quoteinx, {'code':index, 'day':stkday}).fetchall()[0][0])

    print "%s weight accuracy is %.3f%% (%.3f (true data in %s) vs. %.3f (est. from %s))" % (index, ((indexquote2-indexquote3)*100/indexquote3), indexquote3, stkday, indexquote2, wtday)

    wtfn = os.path.join(c_quotedbdir, index+'.wt')
    wtf = open(wtfn, 'wb')
    csvwrter = csv.writer(wtf)
    csvwrter.writerow([wtday,])
    for c in wt:
        csvwrter.writerow([c, wt[c], cwt[c]])
    wtf.close()

    wt = {}
    cwt = {}
