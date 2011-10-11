import pickle
import struct
from datetime import datetime, date, timedelta

class dictdict(dict):
    def __getitem__(self, key):
        if not key in self:
            self.setdefault(key, dict())
        return dict.__getitem__(self, key)

class command:
    def __init__(self):
        self.cmdname = ""
        self.args = []
        self.kwargs = {}

    def __str__(self):
        return "cmdname: %s, args: %s, kwargs: %s" % (
                self.cmdname,
                self.args,
                self.kwargs,
                )

    def pack(self):
        msg = pickle.dumps(self, -1)
        msglen = len(msg)
        return struct.pack("!I", msglen) + msg

def recv_n(conn, n):
    left = n
    content = []
    while 1:
        if left <= 0:
            break
        buf = conn.recv(left)
        content.append(buf)
        left = left - len(buf)

    return "".join(content)

def calsicontracts():
    # if today <= deliver data: this month, next month, next quarter, n-next quarter
    # else: next month, next next month, ...
    today = date.today()
    deliverday = date(today.year, today.month, 1)
    oneday = timedelta(1)
    fridaycount = 0
    contracts = []
    while deliverday < today:
        if deliverday.isoweekday() == 5:
            fridaycount += 1
        deliverday += oneday
    contract = (today.year, today.month)
    if fridaycount >= 3:
        contract = incmonth(contract)

    contracts.append(contract)
    contract = incmonth(contract)
    contracts.append(contract)

    for i in range(2):
        while 1:
            contract = incmonth(contract)
            if contract[1] % 3 == 0:
                contracts.append(contract)
                break
    return [ "".join(("IF", str(year)[2:], "%02d"%month)) for (year, month) in contracts]

def incmonth(yearmonth, inc=1):
    # yearmonth is a (year, month) tuple
    year, month = yearmonth
    for i in range(inc):
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
    return (year, month)

