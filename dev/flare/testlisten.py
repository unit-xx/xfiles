import pickle
import redis
import sys

r = redis.Redis()
p = r.pubsub()
p.subscribe(sys.argv[1])
while 1:
    m = next(p.listen())
    try:
        print pickle.loads(m['data'])
    except:
        print m['data']

# $Id$
