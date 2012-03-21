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
loginok = True
username = 'anonymous'
if not hss.setup():
    loginok = False
else:
    username = hss['client_name']

print username

hss.close()
