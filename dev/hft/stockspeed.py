# stock price changing speed should give hints to HS300 futures.
import sys
from datetime import datetime

from siffilter import *

if __name__=="__main__":
    scodefn = sys.argv[1]
    stockqfn = sys.argv[2]

    scodes = [x.strip() for x in open(scodefn)]
    qf = open(stockqfn)

    tick = None
    tstart = None
    dirfs = {}
    for s in scodes:
        dirfs[s] = DirectionFilter(12)

    for line in qf:
        if line.startswith("==="):
            line = line.strip()
            t = None
            try:
                t = datetime.strptime(line, "=== %Y-%m-%d %H:%M:%S.%f ===")
            except ValueError:
                try:
                    t = datetime.strptime(line, "=== %Y-%m-%d %H:%M:%S ===")
                except ValueError:
                    pass
            # intialize tsindex to the first sample timestamp
            # which is larger than first tick
            if t is not None:
                tick = t
                if tstart is None:
                    tstart = t

                if dirfs[scodes[0]].value() is not None:
                    # should not be None for all dirfs
                    alphas = [x.value()[1] for x in dirfs.values()]
                    alphas.sort(reverse=True)
                    print tick, " ".join("%.5f"%x for x in alphas[0:6])

        else:
            if tick == None:
                continue

            tmp = line.split(",")
            scode = tmp[0]
            if scode in scodes:
                if scode == "000300":# indexes
                    price = float(tmp[7])
                elif scode.startswith("00"):
                    price = float(tmp[4])
                elif scode.startswith("60"):
                    price = float(tmp[7])

                dirfs[scode].feed(((tick-tstart).seconds, price))

