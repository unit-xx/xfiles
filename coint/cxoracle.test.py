#!/usr/bin/python

import cx_Oracle
ip = '172.18.19.37'
port = 1521
sid = 'webdb1'
tns = cx_Oracle.makedsn(ip, port, sid)
print tns
conn = cx_Oracle.connect('beijing', 'beijing', tns)
curs = conn.cursor()

curs.execute('select * from wind.tb_object_1090 where rownum<=2')
print curs.description
for row in curs:
    print row
conn.close()

