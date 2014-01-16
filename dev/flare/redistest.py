import redis
from datetime import datetime, timedelta
from threading import Thread

def seconds(dt):
    return (dt.seconds + dt.microseconds/1000000.0)

n = 10000

r = redis.Redis(host='127.0.0.1')
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

print 'set in redis'

t1 = datetime.now()
for i in range(n):
    r.set('test', 1)
t2 = datetime.now()
print t2-t1, seconds(t2-t1)/n, n/seconds(t2-t1)

print 'get in redis'

t1 = datetime.now()
for i in range(n):
    a = r.get('test')
t2 = datetime.now()
print t2-t1, seconds(t2-t1)/n, n/seconds(t2-t1)

print

print 'publish perf'

def publisher(n, r, ch):
    t1 = datetime.now()
    for i in range(n):
        r.publish(ch, '%d'%i)
    t2 = datetime.now()
    print 'publish %.3f' % n/seconds(t2-t1)


def listener(n, r, ch):
    sub = r.pubsub()
    sub.subscribe(ch)
    t1 = datetime.now()
    for i in range(n):
        msg = next(sub.listen())
    t2 = datetime.now()
    print 'subscribe %.3f' % n/seconds(t2-t1)

Thread(target=listener, args=(10, r, 'test')).start()
Thread(target=publisher, args=(10, r, 'test')).start()

# $Id$ 
