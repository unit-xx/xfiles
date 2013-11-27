import redis
from datetime import datetime, timedelta
from threading import Thread

def seconds(dt):
    return (dt.seconds + dt.microseconds/1000000.0)

n = 10000

r = redis.Redis(host='50.1.8.26')

def publisher(n, r, ch):
    t1 = datetime.now()
    for i in range(n):
        r.publish(ch, '%d'%i)
    t2 = datetime.now()
    print 'publish %.3f' % (n/seconds(t2-t1))


def listener(n, r, ch):
    sub = r.pubsub()
    sub.subscribe(ch)
    t1 = datetime.now()
    for i in range(n):
        msg = next(sub.listen())
    t2 = datetime.now()
    print 'subscribe %.3f' % (n/seconds(t2-t1))

Thread(target=listener, args=(n, r, 'test')).start()
Thread(target=publisher, args=(n, r, 'test')).start()

