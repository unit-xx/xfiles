library(zoo)
library(chron)

Sys.setlocale(category = "LC_TIME", locale = "C")

source('util.r')

qfn.base = '201305'

args = commandArgs(T)
if(length(args) > 0) qfn.base=args[1]

dorev = F
if(length(args) > 1) dorev = (as.numeric(args[2])==-1)
if (dorev)
{
  daytag = 'rev'
} else
{
  daytag = 'norm'
}

options(digits.secs=3) # for milliseconds parsing and display

if1.suf = 'if1'

tstart = Sys.time()

print(sprintf('Reading quotation ... %s (%s)', qfn.base, Sys.time()))
qfn1 = paste(qfn.base, if1.suf, sep='.')
q1 = read.quote(qfn1, trdstart='09:30:00', trdend='15:00:00')
print(sprintf('Reading quotation done ... %s (%s)', qfn.base, Sys.time()))

dayidx = as.POSIXct(trunc(index(q1), 'days'))
days = unique(dayidx)

stopprofit.seq = seq(2.4, 5.0, 0.2)
stoploss.seq = seq(-2.4, -5.0, -0.2)
#stopprofit.seq = 0.4
#stoploss.seq = -0.4

print(sprintf('Backtesting ... %s (%s)', qfn.base, Sys.time()))

allperf = data.frame(stringsAsFactors=F)
alltrace = data.frame(stringsAsFactors=F)
txcost = 0.1

for (i in 1:length(days))
{
  day = days[i]
  idx = which(dayidx == day)
  # daily spread
  dq1 = q1[idx,]
  
  qfirst = dq1$buyprice1[1,][[1]]
  qlast = dq1$buyprice1[NROW(dq1),][[1]]
  
  if ( (qlast>qfirst) & !dorev)
  {
    oprice = 'sellprice1'
    cprice = 'buyprice1'
    daydir = 1
  }else
  {
    oprice = 'buyprice1'
    cprice = 'sellprice1'
    daydir = -1
  }
  
  for (stopprofit in stopprofit.seq)
  {
    for (stoploss in stoploss.seq)
    {
      # do open, ttrace open/close is in tick time, not tick sequence number
      print(sprintf('Backtesting day %s (%s), stop profit %.1f, stop loss %.1f',
                    day, daytag, stopprofit, stoploss))
      
      ttrace = mmzjbt(dq1, stopprofit, stoploss, oprice, cprice, daydir)
      if(NROW(ttrace)>0)
      {
        ttrace = cbind(ttrace, stopprofit=stopprofit, stoploss=stoploss, daydir=daydir)
        alltrace = rbind(alltrace, ttrace)
      }
      # it is ok to compute perf summary when there's no trading
      tperf = mmzjperfsum(ttrace, txcost, day)
      tperf = cbind(tperf, stopprofit=stopprofit, stoploss=stoploss, daydir=daydir)
      allperf = rbind(allperf, tperf)
    }
  }
}

# print(paste('Plotting performance.', Sys.time()))
# mmperffn = paste('mmzjperfplot', qfn.base, 'pdf', sep='.')
# pdf(mmperffn, width=17.55, height=11.07)
# 
# allperf.zoo = zoo(allperf[,-1], allperf[,1])
# barplot(allperf.zoo$ntrd, beside=T, main='# of trades')
# barplot(allperf.zoo[, c('prft', 'prfttx')], beside=T, main='profit tx Off/On')
# barplot(allperf.zoo$daydir, beside=T, main='Day direction')
# 
# dev.off()

# print(paste('Writing trading trace.', Sys.time()))
# 
# tracefn = paste('mmzjtrace', qfn.base, 'csv', sep='.')
# write.csv(alltrace, tracefn, row.names=F)
# 
print(paste('Writing performance.', Sys.time()))
perffn = paste('mmzjperf', daytag, qfn.base, 'csv', sep='.')
write.csv(allperf, perffn, row.names=F)

print(paste('Backtest end.', Sys.time()))

tend = Sys.time()
tdiff = difftime(tend, tstart, units='secs')

print(sprintf('Backtest using %s. (%s per day, %s per (day,param)',
              format(tdiff), 
              format(tdiff/length(days)), 
              format(tdiff/length(days)/length(stopprofit.seq)/length(stoploss.seq))))
