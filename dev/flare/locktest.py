import threading
from datetime import datetime

# test1: create lock
def seconds(dt):
    return (dt.seconds + dt.microseconds/1000000.0)

n = 1000000

t1 = datetime.now()
for i in range(n):
    a = threading.Lock()
t2 = datetime.now()
print t2-t1, seconds(t2-t1)/n, n/seconds(t2-t1)

t1 = datetime.now()
for i in range(n):
    a.acquire()
    a.release()
t2 = datetime.now()
print t2-t1, seconds(t2-t1)/n, n/seconds(t2-t1)

# $Id$ 
