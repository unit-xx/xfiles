import sys
import csv

fna = sys.argv[1]
fa = open(fna, "rb")
ra = csv.reader(fa)
stockalist = []
stocka = {}
for i in ra:
    scode = i[0].upper() + i[1]
    stockalist.append(scode)
    stocka[scode] = int(i[2])

fnb = sys.argv[2]
fb = open(fnb, "rb")
rb = csv.reader(fb)
stockb = {}
for i in rb:
    scode = i[0].upper() + i[1]
    stockb[scode] = int(i[2])

for scode in stockb:
    if scode in stocka:
        stocka[scode] -= stockb[scode]

wc = csv.writer(sys.stdout)
for scode in stockalist:
    wc.writerow([scode[0:2], scode[2:], stocka[scode]])

