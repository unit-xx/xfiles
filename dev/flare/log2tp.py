import sys

fn = sys.argv[1]
for line in open(fn):
    tp = line.split('&')[-1].strip()
    try:
        tpp = [float(x) for x in tp.split()]
        if len(tpp)==6:
            print tp
    except Exception:
        pass

# $Id$ 
