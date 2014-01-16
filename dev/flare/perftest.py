import random
import time
from datetime import datetime
import logging, logging.config

def seconds(dt):
    return (dt.seconds + dt.microseconds/1000000.0)

n = 1000000
t1 = datetime.now()
for i in range(1,n):
    a = random.random()
t2 = datetime.now()
print t2-t1, seconds(t2-t1)/n, n/seconds(t2-t1)

n = 100000
t1 = datetime.now()
for i in range(1,n):
    a = random.random()
    c = (a > 0.0)
t2 = datetime.now()
print t2-t1, seconds(t2-t1)/n, n/seconds(t2-t1)

n = 1000000
a = {}
t1 = datetime.now()
for i in range(1,n):
    a['a'] = 2
    b = a['a']

t2 = datetime.now()
print t2-t1, seconds(t2-t1)/n, n/seconds(t2-t1)

n = 10000
logging.config.fileConfig('config.ini', {"logfn":'perftest.log'})
logger = logging.getLogger()
logger.info('Time to minize cmd window, at your choice.')
time.sleep(1)
t1 = datetime.now()
for i in range(0,n):
    logger.info('A brown fox jump blahblahblah %+2d, %s, %.2f', 12, 'sdfsad', 3.1415926)
t2 = datetime.now()
print t2-t1, seconds(t2-t1)/n, n/seconds(t2-t1)

# $Id$ 
