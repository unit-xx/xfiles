library(zoo)
library(chron)

source('util.r')

Sys.setlocale(category = "LC_TIME", locale = "C")
options(digits.secs=3) # for milliseconds parsing and display

qfn.base = '201305'
args = commandArgs(T)
if(length(args) > 0) qfn.base=args[1]

print(paste('Reading quotation', Sys.time()))

qfn = paste(qfn.base, 'if1', sep='.')
qall = read.quote(qfn)

dayidx = as.POSIXct(trunc(index(qall), 'days'))
days = unique(dayidx)

for (i in 1:length(days))
{
  d = days[i]
  idx = which(dayidx == d)
  qday = qall[idx,]
  
  ttrace = mmhftbt(qday, tintns, sigadj, qmax)
  tperf = mmhftperf(ttrace, txcost, day)
}