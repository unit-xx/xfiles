import redis
from datetime import datetime, timedelta
from threading import Thread

def seconds(dt):
    return (dt.seconds + dt.microseconds/1000000.0)

n = 10000

r = redis.Redis()
a = 0

print 'inc using add operator'

t1 = datetime.now()
for i in range(n):
    a += 1
t2 = datetime.now()
print t2-t1, seconds(t2-t1)/n, n/seconds(t2-t1)

print 'inc in redis'

r.set('test', 1)
t1 = datetime.now()
for i in range(n):
    r.incr('test')
t2 = datetime.now()
print t2-t1, seconds(t2-t1)/n, n/seconds(t2-t1)

print

print 'publish perf'

def publisher(n, r, ch):
    for i in range(n):
        print 'pub %d %s' % (i, datetime.now())
        r.publish(ch, '%d Hello world!'%i)


def listener(n, r, ch):
    sub = r.pubsub()
    sub.subscribe(ch)
    for i in range(n):
        msg = next(sub.listen())
        print 'sub %d %s' % (i, datetime.now())

Thread(target=listener, args=(10, r, 'test')).start()
Thread(target=publisher, args=(10, r, 'test')).start()

