from datetime import date

import util

ifcal = util.IFCalendar()
print ifcal.clist(date(2013, 1, 13))
print ifcal.clist(date(2013, 1, 14))
print ifcal.clist(date(2013, 2, 14))
print ifcal.clist(date(2013, 2, 15))
print ifcal.clist(date(2013, 2, 16))
print ifcal.clist(date(2013, 2, 17))
