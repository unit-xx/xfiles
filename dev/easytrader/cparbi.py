import os
import sys
import ConfigParser
from threading import Thread
import getpass
import time

import jsd

def dowork(jsdsession, openclose, longshort, code, price, share):

    req = jsd.OrderReq(jsdsession)
    resp = jsd.OrderResp(jsdsession)
    if openclose == "open":
        if longshort == "long":
            req.makeopenlong(code, price, share)
        elif longshort == "short":
            req.makeopenshort(code, price, share)
    elif openclose == "close":
        if longshort == "long":
            req.makecloselong(code, price, share)
        elif longshort == "short":
            req.makecloseshort(code, price, share)

    req.send()
    resp.recv()
    print resp.records
    print

def main():
    try:
        mode = sys.argv[1]
        ptfn = sys.argv[2]
    except:
        print "Usage: %s <op-mode> <ptf file>"
        sys.exit(1)

    config = ConfigParser.ConfigParser()
    config.read(ptfn)
    jsdcfg = {}
    for k,v in config.items("jsd"):
        jsdcfg[k] = v
    try:
        jsdcfg["jsdport"] = int(jsdcfg["jsdport"])
    except KeyError:
        jsdcfg["jsdport"] = 9100
    jsdcfg["jsdpasswd"] = getpass.getpass("Password: ")

    jsd1 = jsd.session(jsdcfg)
    jsd2 = jsd.session(jsdcfg)
    if not jsd1.setup() or not jsd2.setup():
        jsd1.close()
        jsd2.close()
        print "cannot setup jsd session."
        sys.exit(1)

    MYSEC = "arbitrage"
    share = config.get(MYSEC, "share")
    longcode = config.get(MYSEC, "long")
    shortcode = config.get(MYSEC, "short")

    ans = raw_input("Ready to arbitrage, go? (y/n): ")
    if ans != "y":
        sys.exit(1)

    if mode == "open":
        t1 = Thread(target=dowork,
                args=(jsd1, "open", "long", longcode, "0.0", share))

        t2 = Thread(target=dowork,
                args=(jsd2, "open", "short", shortcode, "0.0", share))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

    elif mode == "close":
        t1 = Thread(target=dowork,
                args=(jsd1, "close", "long", longcode, "0.0", share))

        t2 = Thread(target=dowork,
                args=(jsd2, "close", "short", shortcode, "0.0", share))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

    else:
        print "unknow operation"

if __name__=="__main__":
    main()
