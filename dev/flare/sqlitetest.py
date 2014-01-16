import sqlite3
from datetime import datetime

def seconds(dt):
    return (dt.seconds + dt.microseconds/1000000.0)
 
conn = sqlite3.connect('./tmp/example')

c = conn.cursor()

# Create table
c.execute('drop table if exists stocks')
c.execute('vacuum')
c.execute('''create table stocks
(date text, trans text, symbol text,
 qty real, price real)''')

# Insert a row of data
n = 100

print('start')
t1 = datetime.now()

for i in range(n):
    c.execute("""insert into stocks
              values ('2006-01-05','BUY','RHAT',100,35.14)""")
    conn.commit()

t2 = datetime.now()
print('end')
print t2-t1, seconds(t2-t1)/n, n/seconds(t2-t1)
# Save (commit) the changes

# We can also close the cursor if we are done with it
conn.commit()
c.close()
conn.close()

# with commit per loop: 0:00:07.293000 0.07293 13.7117784177
# without commit: 0:00:00.053000 5.3e-06 188679.245283

# $Id$ 
