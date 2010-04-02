from dbfpy import dbf
import sys

db = dbf.Dbf("show2003.dbf", ignoreErrors=True)
print type(db[0])
print len(db)
print db[0]['S1']
print db[0][0]
print db[0]
sys.exit(1)

for rec in db:
    print rec
    raw_input()
print

