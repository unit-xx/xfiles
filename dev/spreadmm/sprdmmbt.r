# run and visual selected (d, tintns, sigadj, qmax) mm tradings

library(zoo)
library(chron)

source('util.r')

Sys.setlocale(category = "LC_TIME", locale = "C")
options(digits.secs=3) # for milliseconds parsing and display

qfn.base = '20140214'

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
# wsize and step in ticks
#wsize = 1800 # about 15 minutes
#step = 60 # about 0.5 minute

txcost = 0.2 # per trade, not per pair of trade

tintns = 0.4
sigadj = 0.2

if(length(args) > 3) tintns = as.numeric(args[4])
if(length(args) > 4) sigadj = as.numeric(args[5])

allperf = data.frame(stringsAsFactors=F)

mmtracefn = sprintf('mmbttraceplot.q%02d.t%02d.s%02d.w%d.%s.pdf', qmax, tintns*10, sigadj*10, wsize, qfn.base)
pdf(mmtracefn, width=17.55, height=11.07)
op = par(no.readonly = TRUE)
layout(matrix(c(1,1,2,3,4), 5, 1, byrow=TRUE), respect=F)

for (i in 1:length(days))
{
  d = days[i]
  idx = which(dayidx == d)
  # daily spread
  dsprd = sprd[idx,]
  
  print(sprintf('Plotting %s (day %d)', format(d), i))
  # 2. rolling updated median using wsize
  cc = rollapply(dsprd$midsprd, wsize, median, by=step, align='right')
  cc = na.locf(merge(cc, dsprd$midsprd))$cc
  
  ttrace = mmtrdbt3(dsprd, cc, tintns, sigadj, qmax)
  tperf = mmperfsum(ttrace, txcost, d)
  allperf = rbind(allperf, tperf)
  
  # 1. the midsprd and the trading points
  plot(dsprd$midsprd, type='l', col='grey', main=paste('midsprd for', format(d)))
  lines(cc, col='black') # mid line
  
  if(NROW(ttrace)>0)
  {
    shortick = ttrace$tick[which(ttrace$longshort==-1)]
    longtick = ttrace$tick[which(ttrace$longshort==1)]
    points(dsprd$midsprd[shortick], pch='S')
    points(dsprd$midsprd[longtick], pch='L')
  }
  
  # 2. how q changes
  if(NROW(ttrace)>0)
  {
    qtrace = zoo(ttrace$q, ttrace$tick)
    qtrace = rbind(qtrace, zoo(0, index(dsprd)[1]))
    qtrace = rbind(qtrace, zoo(ttrace$q[length(ttrace$q)], index(dsprd)[NROW(dsprd)]))
  
    plot(qtrace, type='s', col='grey', main=paste('q for', format(d)))
    abline(h=c(qmax, -qmax), lty='dotted')
  }
  else plot(0)
  
  # 3. how wealth changes
  if(NROW(ttrace)>0)
  {
    w = -(ttrace$longshort * ttrace$sprd) - txcost
    w = cumsum(w)
    qzero = which(ttrace$q==0)
    w = w[qzero]
    w.zoo = zoo(w, ttrace$tick[qzero])
    w.zoo = rbind(w.zoo, zoo(0, index(dsprd)[1]))
    w.zoo = rbind(w.zoo, zoo(w[length(w)], index(dsprd)[NROW(dsprd)]))
    plot(w.zoo, type='s', col='grey', main=paste('wealth for', format(d)))
  }
  else plot(0)
  
  # 4. the tsprd and the trading points
  tsprd = dsprd$midsprd-cc
  plot(tsprd, type='l', col='grey', main=paste('tsprd for', format(d)))
  
  if(NROW(ttrace)>0)
  {
    points(tsprd[shortick], pch='S')
    points(tsprd[longtick], pch='L')
  }
}

par(op)

allperf.zoo = zoo(allperf[,-1], allperf[,1])
barplot(allperf.zoo[,c(1,2,3)], beside=T, main='# of trades', col=cm.colors(3))
barplot(allperf.zoo[,4], beside=T, main='# of mismatch', col=cm.colors(3))
barplot(allperf.zoo[,5], main='Profits', col='grey')
barplot(allperf.zoo[,6], main='Implied Cost', col='grey')

dev.off()