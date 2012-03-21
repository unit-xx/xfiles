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

qreq = hs.QueryHistOrderReq(hss)
qreq['start_date'] = '20120319'
qreq['end_date'] = '20120319'
qreq.send()
qresp = hs.QueryHistOrderResp(hss)
qresp.recv()
print qresp.errorno
print qresp.errormsg
for p in qresp.records:
    print p
    print

hss.close()
