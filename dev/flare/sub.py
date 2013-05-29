import redis
import pickle

r = redis.Redis()
sub = r.pubsub()
sub.subscribe('machannel')
while 1:
    qmsg = next(sub.listen())
    if qmsg['type'] == 'message':
        m = pickle.loads(qmsg['data'])
        print m