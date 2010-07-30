import csv
import sys
from datetime import datetime

datefmt = "%m/%d/%Y %H:%M:%S" # 7/21/2010 9:15:28

try:
    r = csv.reader(open(sys.argv[1]))
except IndexError:
    r = csv.reader(sys.stdin)
w = csv.writer(sys.stdout)

def docombine(tocombine):
    tprice = 0.0
    tvol = 0
    for r in tocombine:
        tprice = tprice + r[2] * r[3]
        tvol = tvol + r[3]
    avgprice = tprice / tvol
    tocombine[0][2] = "%0.1f" % avgprice
    tocombine[0][3] = tvol
    tocombine[0][0] = datetime.strftime(tocombine[0][0], datefmt)

tocombine = []
for row in r:
    row[0] = datetime.strptime(row[0], datefmt)
    row[2] = float(row[2])
    row[3] = int(row[3])

    if tocombine == []:
        tocombine.append(row)
    else:
        if row[0] != tocombine[-1][0]:
            # do combine time
            docombine(tocombine)
            w.writerow(tocombine[0])
            del tocombine[:]

        tocombine.append(row)

docombine(tocombine)
w.writerow(tocombine[0])
