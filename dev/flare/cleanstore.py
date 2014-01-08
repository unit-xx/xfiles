import redis

import config

rsec = 'redis'
cfg = config.parseconfig()
rcfg = cfg[rsec]
rcfg['port'] = int(rcfg['port'])
rcfg['db'] = int(rcfg['db'])

r = redis.Redis(**rcfg)
okey = r.keys('ORDER*')
tkey = r.keys('TRADE*')
aok = r.keys('ALLORDER*')
apk = r.keys('ALLPOS*')
pkey = r.keys('POSITION*')
if len(okey)>0:
    r.delete(*okey)
if len(tkey)>0:
    r.delete(*tkey)
if len(aok)>0:
    r.delete(*aok)
if len(apk)>0:
    r.delete(*apk)
if len(pkey)>0:
    r.delete(*pkey)

okey = r.keys('ORDER*')
tkey = r.keys('TRADE*')
aok = r.keys('ALLORDER*')
apk = r.keys('ALLPOS*')
pkey = r.keys('POSITION*')
print okey
print tkey
print aok
print apk
print pkey
