import hs
import ConfigParser

HSSEC = 'hs'
MYSEC = "metatrader"

CONFIGFN = "metatrader.cfg"
config = ConfigParser.RawConfigParser()
config.read(CONFIGFN)

hscfg = {}
for k,v in config.items(HSSEC):
    hscfg[k] = v
hscfg["hsport"] = int(hscfg["hsport"])
hscfg["protocol"] = int(hscfg["protocol"])
hscfg["keyciper"] = int(hscfg["keyciper"])

hss = hs.session(hscfg)
if not hss.setup():
    print "cannot login"
    sys.exit(1)

breq = hs.OrderReq(hss)
breq.bsStock('SH', 'BUY', '600003', '88.90', '200')
bresp = hs.OrderResp(hss)
bresp.recv()
print bresp.errorno
print bresp.errormsg
for p in bresp.records:
    print p
    print

hss.close()
