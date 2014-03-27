library(chron)
library(zoo)
library(tseries)
library(moments)

Sys.setlocale(category = "LC_TIME", locale = "C")
options(digits.secs=3) # for milliseconds parsing and display

source('util.r')

trdintense <- function(tsprd)
{
  tkurt = kurtosis(tsprd, na.rm=T)
  tskew = skewness(tsprd, na.rm=T)
  
  # get around possible 0.05 in cc, which is rolling median on dsprd
  t2 = round(abs(tsprd), 1)
  h = hist(t2, breaks=seq(min(t2, na.rm=T), max(t2, na.rm=T), 0.1), plot=F)
  
  o = which(h$intensities>0)
  intense = h$intensities[o]
  mids = h$mids[o]
  
  k = -coef(lm(log(intense) ~ mids))[2]
  return(c(tkurt, tskew, k))
}

tsstats <- function(ts)
{
  ret = c(max(ts, na.rm=T), min(ts, na.rm=T), mean(ts, na.rm=T), median(ts, na.rm=T),
          sd(ts, na.rm=T), 
    skewness(ts, na.rm=T), kurtosis(ts, na.rm=T), adf.test(ts)$p.value,
    ouhlife(ts))
  return(ret)
}

qfn.base = '201305'
tunit = 'days'

args = commandArgs(T)
if(length(args) > 0) qfn.base=args[1]

print(sprintf('Reading spread ... %s (%s)', qfn.base, Sys.time()))

sprdfn = paste('sprd', qfn.base, 'csv', sep='.')
sprd = read.sprd(sprdfn)

dayidx = as.POSIXct(trunc(index(sprd), tunit))
days = unique(dayidx)

print(sprintf('Stats for raw spread ... %s (%s)', qfn.base, Sys.time()))

# aggregate by day, for several daily statistics.
rsprdstats = aggregate(sprd$midsprd, by=dayidx, tsstats)
names(rsprdstats) = c('max', 'min', 'mean', 'median', 'sd', 
                    'skewness', 'kurtosis', 'adf.pvalue','hlife')

print(sprintf('Stats for MA and tsprd ... %s (%s)', qfn.base, Sys.time()))

wsize = 1800 # about 15 minutes
step = 120 # about 1 minute

ccstats = data.frame(stringsAsFactors=F)
dccstats = data.frame(stringsAsFactors=F)
tsprdstats = data.frame(stringsAsFactors=F)

for (i in 1:length(days))
{
  d = days[i]
  idx = which(dayidx == d)
  # daily spread
  dsprd = sprd[idx,]

  cc = rollapply(dsprd$midsprd, wsize, median, by=step, align='right')
  cc = na.locf(merge(cc, dsprd$midsprd))$cc
  cc = na.omit(cc)
  
  tsprd = dsprd$midsprd - cc
  
  ccstats = rbind(ccstats, tsstats(coredata(cc)))
  dccstats = rbind(dccstats, tsstats(diff(coredata(cc))))
  tsprdstats = rbind(tsprdstats, tsstats(coredata(tsprd)))
}

names(ccstats) = c('max', 'min', 'mean', 'median', 'sd', 
                      'skewness', 'kurtosis', 'adf.pvalue','hlife')
names(dccstats) = c('max', 'min', 'mean', 'median', 'sd', 
                   'skewness', 'kurtosis', 'adf.pvalue','hlife')
names(tsprdstats) = c('max', 'min', 'mean', 'median', 'sd', 
                      'skewness', 'kurtosis', 'adf.pvalue','hlife')

ccstats = zoo(ccstats, days)
dccstats = zoo(dccstats, days)
tsprdstats = zoo(tsprdstats, days)

print(sprintf('Writing stats ... %s (%s)', qfn.base, Sys.time()))

sprdfn = paste('sprdstats', 'raw', tunit, qfn.base, 'csv', sep='.')
write.zoo(rsprdstats, sprdfn, row.names=F, sep=',', index.name='day')

ccfn = paste('sprdstats', 'cc', tunit, qfn.base, 'csv', sep='.')
write.zoo(ccstats, ccfn, row.names=F, sep=',', index.name='day')

dccfn = paste('sprdstats', 'dcc', tunit, qfn.base, 'csv', sep='.')
write.zoo(dccstats, dccfn, row.names=F, sep=',', index.name='day')

tsprdfn = paste('sprdstats', 'tsprd', tunit, qfn.base, 'csv', sep='.')
write.zoo(tsprdstats, tsprdfn, row.names=F, sep=',', index.name='day')
