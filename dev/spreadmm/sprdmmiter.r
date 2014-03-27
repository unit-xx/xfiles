library(chron)
library(zoo)
library(tseries)
library(moments)

print(paste('begin.', Sys.time()))
Sys.setlocale(category = "LC_TIME", locale = "C")
options(digits.secs=3) # for milliseconds parsing and display

source('util.r')

qfn.base = '201305'

args = commandArgs(T)
if(length(args) > 0) qfn.base=args[1]

qmax = 1
if(length(args) > 1) qmax=as.integer(args[2])

wsize = 120 # about 1 minutes
if(length(args) > 2) wsize=as.integer(args[3])
if (wsize >= 120) step = 60 else step = wsize/2

print(paste('Reading spread', Sys.time()))
sprdfn = paste('sprd', qfn.base, 'csv', sep='.')
sprd = read.sprd(sprdfn)

dayidx = as.POSIXct(trunc(index(sprd), 'days'))
days = unique(dayidx)

# backtest by day

txcost = 0.2 # per spread trade, not per pair of spread trade

print('Iterative backtest day by day.')

tintns.seq = seq(0.2, 1.2, 0.05)
sigadj.seq = seq(0.1, 0.6, 0.05)

print(paste('Iterative mm backtesting', Sys.time()))

tstart = Sys.time()
alltrace = data.frame(stringsAsFactors=F)
allperf = data.frame(stringsAsFactors=F)
for (i in 1:length(days))
#for (i in 1:5)
{
  d = days[i]
  idx = which(dayidx == d)
  # daily spread
  dsprd = sprd[idx,]
 
  print(sprintf('Backtesting %s (day %d) %s', format(d), i, format(Sys.time())))
  # 2. rolling updated median using wsize
  cc = rollapply(dsprd$midsprd, wsize, median, by=step, align='right')
  cc = na.locf(merge(cc, dsprd$midsprd))$cc
  
  for (tintns in tintns.seq)
  {
    for (sigadj in sigadj.seq)
    {
      #print(sprintf('  on (tintns, sigadj)=(%.2f, %.2f)', tintns, sigadj))
      ttrace = mmtrdbt3(dsprd, cc, tintns, sigadj, qmax)
      if(NROW(ttrace)>0)
      {
        ttrace = cbind(ttrace)
        alltrace = rbind(alltrace, ttrace)
      }
      # it is ok to compute perf summary when there's no trading
      tperf = mmperfsum(ttrace, txcost, d)
      tperf = cbind(tperf, tintns=tintns, sigadj=sigadj)
      allperf = rbind(allperf, tperf)
    }
  }
}

shortrd = which(alltrace$longshort==-1)
longtrd = which(alltrace$longshort==1)

chkshort = all(alltrace$sprd[shortrd]==alltrace$bidsprd[shortrd])
chklong = all(alltrace$sprd[longtrd]==alltrace$asksprd[longtrd])
print(paste('check trace: sprd constraint is', all(chkshort, chklong), Sys.time()))

chkshort = all(alltrace$longdelta[longtrd]>alltrace$delta_b[longtrd])
chklong = all(alltrace$shortdelta[shortrd]>alltrace$delta_a[shortrd])
print(paste('check trace: delta constraint is', all(chkshort, chklong), Sys.time()))

print(paste('check trace: qmax constraint is', all(abs(alltrace$q)<=qmax), Sys.time()))

tend = Sys.time()
tdiff = difftime(tend, tstart, units='secs')

print(paste('Writing trading trace and performance.', Sys.time()))

tracefn = paste('mmiterbttrace', qfn.base, paste('q',qmax,sep=''), paste('w',wsize,sep=''), 'csv', sep='.')
write.csv(alltrace, tracefn, row.names=F)

perffn = paste('mmiterbtperf', qfn.base, paste('q',qmax,sep=''), paste('w',wsize,sep=''), 'csv', sep='.')
write.csv(allperf, perffn, row.names=F)
print(paste('end.', Sys.time()))

print(sprintf('Program performance: total %s, %s per day, %s per (day, param)',
              format(tdiff), 
              format(tdiff/length(days)), 
              format(tdiff/length(days)/length(tintns.seq)/length(sigadj.seq))
              ))
