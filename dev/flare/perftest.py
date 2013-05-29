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

