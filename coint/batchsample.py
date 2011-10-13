#!/usr/bin/python

# generate batch .in/.out samples for testing.

import sys, csv, os

os.putenv('NLS_LANG', 'SIMPLIFIED CHINESE_CHINA.ZHS16GBK')
#os.putenv('NLS_LANG', 'AL32UTF8')
import cx_Oracle

# TODO: read from config
outdir = 'data'
codefn = sys.argv[1]
istart = '20010101'
iend = '20101231'
ostart = '20110101'
oend = '20110930'

ip = '172.18.19.37'
port = 1521
sid = 'webdb1'
user='beijing'
passwd='beijing'

force=False # force overwrite old, otherwise skip existing sample

def main():
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

    q = """
select 
    F16_1090 as code
    ,ob_object_name_1090 as name
    ,F4_1120 as preclose
    ,F5_1120 as open
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
    and F4_1120 is not NULL
    --and rownum <=2
order by "DATE"
    """
    for code in scodes:
        print code, '...',

        ifn = code+'.in'
        ofn = code+'.out'
        if os.path.exists(ifn) or os.path.exists(ofn):
            if not force:
                print 'skipped'
                continue
            else:
                print '(overwrite old sample)',

        iff = open(ifn, 'wb')
        off = open(ofn, 'wb')
        iwriter = csv.writer(iff)
        owriter = csv.writer(off)

        #print q
        curs.execute(q, {'code':code})
        #print conn.encoding
        #print curs.description

        # write headers
        dateindex = 0
        tmp = []
        for i, d in enumerate(curs.description):
            tmp.append(d[0])
            if d[0] == 'DATE':
                dateindex = i
        iwriter.writerow(tmp)
        owriter.writerow(tmp)

        # write data
        for row in curs:
            rdate = row[dateindex]
            if rdate >= istart and rdate <= iend:
                iwriter.writerow(row)
            if rdate >= ostart and rdate <= oend:
                owriter.writerow(row)

        iff.close()
        off.close()

        print 'done'

    conn.close()

if __name__=="__main__":
    main()

