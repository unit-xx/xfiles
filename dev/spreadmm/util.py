from datetime import datetime, timedelta, date


class IFCalendar:
    # given a date, find contract name for IF1/2/3/4, i.e., IF1309, IF1310, IF1312, IF1303
    # methods: date -> deliver day -> contract names
    def __init__(self):
        self.dlvrdays = {} # year/month -> deliver day
        self.contracts = {}
        self.contracts[0] = {} # contract for IF1 -> all contract names
        self.contracts[1] = {}
        self.contracts[2] = {}

    def dlvrday(self, ym):
        if ym in self.dlvrdays:
            dd = self.dlvrdays[ym]
        else:
            dd = date(ym[0], ym[1], 1)
            oneday = timedelta(1)
            fridaycount = 0
            while 1:
                if dd.isoweekday() == 5:
                    fridaycount += 1
                if fridaycount == 3:
                    break
                dd += oneday
            self.dlvrdays[ym] = dd

        return dd

    def clist(self, d, otype=2):
        # d is a date obj
        # otype=0, ret is (year, month) pairs
        # otype=1, ret is "1301" lists
        # otype=2, ret is "IF1301" lists
        ym = (d.year, d.month)

        # find/calc deliver day for a given date (year, month)
        dd = self.dlvrday(ym)

        # contract name for IF1
        if1 = ym
        if d > dd:
            if1 = incmonth(if1)

        # all contracts
        if if1 not in self.contracts:
            contracts = []
            contracts.append(if1)
            if2 = incmonth(if1)
            contracts.append(if2)

            if34 = if2
            for i in range(2):
                while 1:
                    if34 = incmonth(if34)
                    if if34[1] % 3 == 0:
                        contracts.append(if34)
                        break
            self.contracts[0][if1] = contracts
            self.contracts[1][if1] = ['%02d%02d'%(x[0]-2000, x[1]) for x in contracts]
            self.contracts[2][if1] = ['IF%02d%02d'%(x[0]-2000, x[1]) for x in contracts]
        return self.contracts[otype][if1]

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
