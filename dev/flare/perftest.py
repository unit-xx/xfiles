import random
from datetime import datetime

def seconds(dt):
    return (dt.seconds + dt.microseconds/1000000.0)

n = 0.0
t1 = datetime.now()
for i in range(1,10000):
    a = random.random()
    n += a
t2 = datetime.now()
print t2-t1, seconds(t2-t1)/n, n/seconds(t2-t1)

t1 = datetime.now()
for i in range(1,10000):
    a = random.random()
    c = (a > n)
t2 = datetime.now()
print t2-t1, seconds(t2-t1)/n, n/seconds(t2-t1)

b = []
for i in range(0,10000):
    b.append({'a':1})

t1 = datetime.now()
for i in range(0,10000):
    a = b[i]['a']
t2 = datetime.now()
print t2-t1, seconds(t2-t1)/n, n/seconds(t2-t1)
