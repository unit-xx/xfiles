import pickle
import redis
import sys
import datetime

r = redis.Redis()
p = r.pubsub()
p.subscribe(sys.argv[1])
while 1:
    m = next(p.listen())
    try:
        data = pickle.loads(m['data'])
    except:
        data = m['data']

    print str(datetime.datetime.now()), data

# $Id$
