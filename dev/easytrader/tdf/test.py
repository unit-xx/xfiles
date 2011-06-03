from base22 import *
from binascii import hexlify
import datetime
import sys

config = {}
config["tdfserver"] = "172.18.20.141"
config["tdfport"] = 10000

s = session(config)
s.setup()

login = loginReq(s)
login.login("2", "2")

lresp = loginResp(s)
lresp.recv()
lresp.getmkts()
print lresp.markets

ctblreq = codetblReq(s)
for m in lresp.markets:
    ctblreq.getcodetbl(m)
    ctblresp = codetblResp(s)
    ctblresp.recv()
    #ctblresp.getitems()
    print ctblresp.mktcode
    for i in ctblresp.items:
        print i
    #print ctblresp.items
    print

for m in lresp.markets:
    qreq = getquoteReq(s)
    qreq.getquote(m)

rfact = respfactory(s)
while 1:
    resp = rfact.dispatch()
    print "code", resp.code
    if resp.code == ID_TDFTELE_INDEXDATA:
        #print resp.paramlen, len(resp.payload)
        for i in resp.items:
            print i
