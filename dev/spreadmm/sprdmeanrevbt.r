library(chron)
library(zoo)
library(tseries)
library(moments)

Sys.setlocale(category = "LC_TIME", locale = "C")

qfn.base = '201301'

args = commandArgs(T)
if(length(args) > 0) qfn.base=args[1]

options(digits.secs=3) # for milliseconds parsing and display

if1.suf = 'if1'
if2.suf = 'if2'

print(sprintf('Processing ... %s', qfn.base))

qfn1 = paste(qfn.base, if1.suf, sep='.')
qfn2 = paste(qfn.base, if2.suf, sep='.')

readquote <- function(qfn)
{
  q1 = read.table(qfn, header=T, quote="\"", stringsAsFactors=F, 
                  colClasses=c('character','character','integer',
                               'character','numeric','numeric','numeric','numeric'))
  
  # dates and times series as zoo index
  dts = dates(q1$tradeday, format="ymd")
  tms = times(q1$tradetime, format='h:m:s')
  
  # trading hour
  trdstart = '09:20:00'
  trdend = '15:10:00'
  tradeintval = which(tms > times(trdstart) & tms < times(trdend))
  
  tindex = as.POSIXct(paste(q1$tradeday, q1$tradetime), format="%Y%m%d %H:%M:%OS")
  
  q1.zoo = zoo(q1[,c(3,5,6,7,8)], tindex)
  q1.zoo = q1.zoo[tradeintval,]
}

print('Reading Quotations.')
q1.zoo = readquote(qfn1)
q2.zoo = readquote(qfn2)

# merge by 'outer join'
qa = merge(q1.zoo, q2.zoo, all=T, suffixes=c('q1', 'q2'))
# fill gap with latest updates
qa2 = na.locf(qa, na.rm=T) # fill gap with last quotation update

bidsprd = qa2$buyprice1.q2 - qa2$sellprice1.q1
asksprd = qa2$sellprice1.q2 - qa2$buyprice1.q1
midsprd = (bidsprd+asksprd)/2
badiff = asksprd-bidsprd
sprd = cbind(bidsprd, asksprd, midsprd, badiff)
# remove the NAs in the first line for the extreme case
sprd = na.locf(sprd, na.rm=T)

dayidx = as.POSIXct(trunc(index(sprd), 'days'))
days = unique(dayidx)

# backtest by day
wsize = 1800 # about 15 minutes
step = 120 # about 1 minute

minbadiff = 0.8
txcost = 0.4
mincost = minbadiff + txcost
estep = 1.0 + 0.05 # 0.05 as the mid of price unit(0.1)
nstep = 2

trdstats <- function(trace)
{
  if(NROW(trace)>0)
  {
    return(c(NROW(trace), 
      sum(trace$prft), 
      mean(trace$prft),
      sd(trace$prft)
      ))
  }
  else
  {
    return(c(0,0,0,0))
  }
}

trdbt <- function(otick, ctick, tsprd, dsprd, txcost, longshort=c(-1,1))
{
  # algo: open close on the first doable tick. Wait for close
  # after open, no other actions are taken. 
  
  if(length(otick) == 0)
  {
    return(data.frame(stringsAsFactors=F))
  }
  
  otrace = c()
  oid = otick[1]
  etrace = c()
  otrace = c(otrace, oid)
  while(T)
  {
    cid = ctick[findInterval(oid, ctick) + 1]
    if(is.na(cid)) break
    etrace = c(etrace, cid)
    
    oid = otick[findInterval(cid, otick) + 1]
    if(is.na(oid)) break
    otrace = c(otrace, oid)
  }
  
  # pair open/close, deal with dangling open. use cbind, rep
  if(length(otrace) > length(etrace))
  {
    etrace = c(etrace, rep(NROW(tsprd), length(otrace) - length(etrace)))
  }
  ttrace = cbind(otrace, etrace, longshort)
  ttrace = as.data.frame(ttrace)
  
  if(longshort==-1)
  {
    osprd = as.vector(dsprd$bidsprd[otrace,])
    csprd = as.vector(dsprd$asksprd[etrace,])
  } else {
    osprd = as.vector(dsprd$asksprd[otrace,])
    csprd = as.vector(dsprd$bidsprd[etrace,])
  }

  otime = index(dsprd)[otrace]
  obid = as.vector(dsprd$bidsprd[otrace,])
  oask = as.vector(dsprd$asksprd[otrace,])
  obadiff = as.vector(dsprd$badiff[otrace,])
  omid = as.vector(dsprd$midsprd[otrace,])
  occ = as.vector(cc[otrace,])
  
  ctime = index(dsprd)[etrace]
  cbid = as.vector(dsprd$bidsprd[etrace,])
  cask = as.vector(dsprd$asksprd[etrace,])
  cbadiff = as.vector(dsprd$badiff[etrace,])
  cmid = as.vector(dsprd$midsprd[etrace,])
  ccc = as.vector(cc[etrace,])
  
  tosprd = as.vector(tsprd[otrace,])
  tcsprd = as.vector(tsprd[etrace,])
  
  prft = longshort*(csprd - osprd) - txcost
  ttrace = cbind(ttrace, otime, ctime,
                  tosprd, tcsprd, 
                  osprd, obid, oask, obadiff, omid, occ, 
                  csprd, cbid, cask, cbadiff, cmid, ccc,
                  prft)
  return(ttrace)
}

mrevtrdbt <- function(otick, ctick, tsprd, dsprd, txcost, longshort=c(-1,1))
{
  # positive threshold for greater than cc
  
  # otick: (long) dsprd$ask-cc < -(open threshold)
  # ctick: (long) dsprd$bid-cc > -(close threshold)
  
  # otick: (short) dsprd$bid-cc > open threshold
  # ctick: (short) dsprd$ask-cc < close threshold 
}

# cc is the midline of dsprd. At time t, dsprd has three components: mid, bid, ask

sprdfn = paste('sprdtrdbt', qfn.base, 'pdf', sep='.')
pdf(sprdfn, width=17.55, height=11.07)

statshort = data.frame(stringsAsFactors=F)
statlong = data.frame(stringsAsFactors=F)
statall = data.frame(stringsAsFactors=F)

op = par(mfrow=c(2,1))

shorttrace = data.frame(stringsAsFactors=F)
longtrace = data.frame(stringsAsFactors=F)
daytrace = data.frame(stringsAsFactors=F)

print('Backtest by day.')
for (i in 1:length(days))
{
  d = days[i]
  idx = which(dayidx == d)
  # daily spread
  dsprd = sprd[idx,]
  
  # 2. rolling updated mean using wsize
  cc = rollapply(dsprd$midsprd, wsize, median, by=step, align='right')
  cc = na.locf(merge(cc, dsprd$midsprd))$cc
  #cc = na.locf(cc)
  # cc2 is almost same as cc
  #cc2 = rollapply(dsprd$midsprd, wsize, median, by=1, align='right')
  #cc2 = na.locf(merge(cc2, dsprd$midsprd))$cc2
  
  tsprd = dsprd$midsprd - cc
  
  # find signal for shorts
  otsprd = dsprd$bidsprd - cc
  ctsprd = dsprd$asksprd - cc
  otick = which(otsprd>(mincost/2+estep))
  ctick = which(ctsprd<(-mincost/2-0.05)) # asymmetric close
  
  ttrace1 = trdbt(otick, ctick, tsprd, dsprd, txcost, -1)
  
  # reverse otick/ctick for long trading.
  otsprd = dsprd$asksprd - cc
  ctsprd = dsprd$bidsprd - cc
  otick = which(tsprd<(-mincost/2-estep))
  ctick = which(tsprd>(mincost/2+0.05)) # asymmetric close

  ttrace2 = trdbt(otick, ctick, tsprd, dsprd, txcost, 1)
  
  ttrace = rbind(ttrace1, ttrace2)
  daytrace = rbind(daytrace, ttrace)

  #plot(dsprd$midsprd, col='grey')
  
  # visual trading
  #arrows(index(dsprd$midsprd)[ttrace2[,1]], as.vector(dsprd$midsprd[ttrace2[,1],]), 
  #       index(dsprd$midsprd)[ttrace2[,2]], as.vector(dsprd$midsprd[ttrace2[,2],])
  #       )
  # stats
  statshort = rbind(statshort, trdstats(ttrace1))
  statlong = rbind(statlong, trdstats(ttrace2))
  statall = rbind(statall, trdstats(ttrace))
  
  plot(dsprd$midsprd, type='s', col='grey', main=paste('midsprd for', format(d)))
  lines(cc, col='black') # mid line
  lines(cc+mincost/2+estep, col='blue') # short lines
  lines(cc-mincost/2, col='pink')
  lines(cc-mincost/2-estep, col='red') # long lines
  lines(cc+mincost/2, col='lightblue')
  points(dsprd$midsprd[ttrace1$otrace,], pch='o')
  points(dsprd$midsprd[ttrace1$etrace,], pch='c')
  points(dsprd$midsprd[ttrace2$otrace,], pch='o')
  points(dsprd$midsprd[ttrace2$etrace,], pch='c')
  
  plot(tsprd, col='grey', main=paste('tsprd for', format(d)))
  abline(h=mincost/2+estep, col='blue')
  abline(h=-mincost/2, col='pink')
  abline(h=-mincost/2-estep, col='red')
  abline(h=mincost/2, col='lightblue')
  points(tsprd[ttrace1$otrace,], pch='o')
  points(tsprd[ttrace1$etrace,], pch='c')
  points(tsprd[ttrace2$otrace,], pch='o')
  points(tsprd[ttrace2$etrace,], pch='c')
}

par(op)

tracefn = paste('sprdtrdbt', qfn.base, 'csv', sep='.')
write.csv(daytrace, tracefn, row.names=F)

print('Plotting summary.')
ntrd = zoo(cbind(statall[,1], statshort[,1], statlong[,1]), days)
tprft = zoo(cbind(statall[,2], statshort[,2], statlong[,2]), days)
avgprft = zoo(cbind(statall[,3], statshort[,3], statlong[,3]), days)
sdprft = zoo(cbind(statall[,4], statshort[,4], statlong[,4]), days)

barplot(ntrd, beside=T, main='# of trades', col=cm.colors(3))
barplot(tprft, beside=T, main='total profits', col=cm.colors(3))
barplot(avgprft, beside=T, main='avg profits per trade', col=cm.colors(3))
barplot(sdprft, beside=T, main='stdev of profits per trade', col=cm.colors(3))
dev.off()
