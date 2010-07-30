# combine volumn data from ticker to specified precision

import csv
import sys
from datetime import datetime, timedelta

interval = timedelta(seconds=5*60)
offset = timedelta(seconds=0)
maspan = timedelta(seconds=60)
emaalpha = 0.5
datefmt = "%m/%d/%Y %H:%M:%S" # 7/21/2010 9:15:28

r = csv.reader(sys.stdin)
try:
    r = csv.reader(open(sys.argv[1]))
except IndexError:
    pass
except IOError:
    pass
w = csv.writer(sys.stdout)
try:
    interval = timedelta(seconds=int(sys.argv[2]))
    offset = timedelta(seconds=int(sys.argv[3]))
except IndexError:
    pass

def docombine(tocombine):
    tvol = 0
    tprice = 0.0
    for r in tocombine:
        tvol = tvol + r[3]
        tprice = tprice + r[2] * r[3]
    avgprice = tprice / tvol
    for r in tocombine:
        r[3] = tvol
        r[2] = "%0.1f" % avgprice
        r[0] = datetime.strftime(r[0], datefmt)

tocombine = []
starttime = None
offsetskipped = False
w.writerow(["time", "type", 'price', 'vol', 'ma', 'ema', 'wa', 'momentum'])
for row in r:
    row[0] = datetime.strptime(row[0], datefmt)
    row[2] = float(row[2])
    row[3] = int(row[3])

    # skip offset
    while not offsetskipped:
        if starttime == None:
            starttime = row[0]
        else:
            if row[0] - starttime >= offset:
                offsetskipped = True

    # combine by time interval
    if tocombine == []:
        tocombine.append(row)
    else:
        if row[0] - tocombine[0][0] >= interval:
            # process and clear tocombine
            docombine(tocombine)
            for r in tocombine:
                w.writerow(r)
            del tocombine[:]

        tocombine.append(row)

docombine(tocombine)
for r in tocombine:
    w.writerow(r)
