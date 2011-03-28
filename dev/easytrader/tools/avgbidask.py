# average bid-ask prices from b5 to a5

import sys, os
import gzip

qfn = sys.argv[1]
qf = gzip.open(qfn)

shasksum = {}
shbidsum = {}
szasksum = {}
szbidsum = {}
levels = [1,2,3,4,5]
qcount = 0

shaskmap = {1:17,2:19,3:21,4:27,5:29}
shbidmap = {1:12,2:14,3:16,4:23,5:25}
szaskmap = {1:24,2:22,3:20,4:18,5:16}
szbidmap = {1:26,2:28,3:30,4:32,5:34}

# calculate sum for ask/bid inventory 
for line in qf:
    if line.startswith("==="):
        continue

    q = line.split(",")
    code = q[0]
    if code == "000300":
        continue

    qcount = qcount + 1
    if code[0] == "6":
        if code not in shasksum:
            shasksum.setdefault(code, {})
            shbidsum.setdefault(code, {})

        for level in levels:
            shasksum[code].setdefault(level, 0)
            shbidsum[code].setdefault(level, 0)

            shasksum[code][level] = shasksum[code][level] + int(q[shaskmap[level]])
            shbidsum[code][level] = shbidsum[code][level] + int(q[shbidmap[level]])

    elif code[0] == "0":
        if code not in szasksum:
            szasksum.setdefault(code, {})
            szbidsum.setdefault(code, {})

        for level in levels:
            szasksum[code].setdefault(level, 0)
            szbidsum[code].setdefault(level, 0)

            szasksum[code][level] = szasksum[code][level] + int(q[szaskmap[level]])
            szbidsum[code][level] = szbidsum[code][level] + int(q[szbidmap[level]])

# get average
for code in shasksum:
    for level in levels:
        shasksum[code][level] = shasksum[code][level] / qcount
        shbidsum[code][level] = shbidsum[code][level] / qcount

for code in szasksum:
    for level in levels:
        szasksum[code][level] = szasksum[code][level] / qcount
        szbidsum[code][level] = szbidsum[code][level] / qcount

# print them all
shcodes = shasksum.keys()
szcodes = szasksum.keys()
shcodes.sort()
szcodes.sort()
for code in shcodes:
    print code,
    for level in levels:
        print shasksum[code][level],
    for level in levels:
        print shbidsum[code][level],
    print

for code in szcodes:
    print code,
    for level in levels:
        print szasksum[code][level],
    for level in levels:
        print szbidsum[code][level],
    print
