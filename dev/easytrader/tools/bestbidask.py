# calculate best bid/ask level for a portfolio

import sys

ptfn = sys.argv[1]
bestatfn = sys.argv[2]

bestba = {}
for line in open(ptfn):
    mkt, code, count = line.split(",")
    if mkt in ("SH","SZ"):
        bestba.setdefault(code, {})
        bestba[code]["count"] = int(count)/100

for line in open(bestatfn):
    stats = line.split()
    stats[1:] = [int(x) for x in stats[1:]]
    code = stats[0]
    bidcount = 0
    bestba[code]["b"] = -1
    for i in range(1, 6):
        bidcount = bidcount + stats[i]
        if bidcount >= bestba[code]["count"]:
            bestba[code]["b"] = i
            break
    askcount = 0
    bestba[code]["a"] = -1
    for i in range(6, 11):
        askcount = askcount + stats[i]
        if askcount >= bestba[code]["count"]:
            bestba[code]["a"] = i - 5
            break

codes = bestba.keys()
codes.sort()
for c in codes:
    print c, bestba[c]["count"], bestba[c]["b"], bestba[c]["a"]
