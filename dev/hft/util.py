from datetime import date, timedelta

def calsicontracts(day=None):
    # if today <= deliver data: this month, next month, next quarter, n-next quarter
    # else: next month, next next month, ...
    if day is None:
        today = date.today()
    elif type(day) == type(""):
        today = date(int(day[0:4]), int(day[4:6]), int(day[6:8]))

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
    return [ "".join((str(year)[2:], "%02d"%month)) for (year, month) in contracts]

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

def getcross(n, mid):
    # n is a array of numbers
    # return how many times the array goes across the horizential `mid'
    count = 0
    tmp = [int(x < mid) for x in n]
    for i, v in enumerate(tmp[1:], 1):
        if v != tmp[i-1]:
            count = count + 1
    return count
