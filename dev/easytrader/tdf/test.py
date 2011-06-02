from base22 import *
from binascii import hexlify

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
    ctblresp.getitems()
    print ctblresp.mktcode
    print ctblresp.items
    print

for m in lresp.markets:
    qreq = getquoteReq(s)
    qreq.getquote(m)

while 1:
    resp = response(s)
    resp.recv()
    print resp.code
