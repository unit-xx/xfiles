library(chron)
library(zoo)
library(tseries)
library(moments)

#Sys.setlocale(category = "LC_TIME", locale = "C")

ouhlife <- function(x)
{
  s = as.vector(x)
  ds = diff(s)
  smean= mean(s)
  s = s[-length(s)] - smean
  rst = lm(ds ~ s + 0)
  hlife = -log(2)/coef(rst)[1]
  hlife
}

qfn.base = '201301'

args = commandArgs(T)
if(length(args) > 0) qfn.base=args[1]

options(digits.secs=3) # for milliseconds parsing and display

if1.suf = 'if1'
if2.suf = 'if2'

print(sprintf('Processing ... %s', qfn.base))

qfn1 = paste(qfn.base, if1.suf, sep='.')
qfn2 = paste(qfn.base, if2.suf, sep='.')

q1 = read.table(qfn1, header=T, quote="\"", stringsAsFactors=F, 
                colClasses=c('character','character','integer',
                             'character','numeric','numeric','numeric','numeric'))

# dates and times series as zoo index
dts = dates(q1$tradeday, format="ymd")
tms = times(q1$tradetime, format='h:m:s')

# trading hour
tradeintval = which(tms > times('09:20:00') & tms < times('15:10:00'))

tindex = as.POSIXct(paste(q1$tradeday, q1$tradetime), format="%Y%m%d %H:%M:%OS")

q1.zoo = zoo(q1[,c(3,5,6,7,8)], tindex)
q1.zoo = q1.zoo[tradeintval,]

q2 = read.table(qfn2, header=T, quote="\"", stringsAsFactors=F, 
                colClasses=c('character','character','integer',
                             'character','numeric','numeric','numeric','numeric'))

# dates and times series as zoo index
dts = dates(q2$tradeday, format="ymd")
tms = times(q2$tradetime, format='h:m:s')

# trading hour
tradeintval = which(tms > times('09:20:00') & tms < times('15:10:00'))

tindex = as.POSIXct(paste(q2$tradeday, q2$tradetime), format="%Y%m%d %H:%M:%OS")

q2.zoo = zoo(q2[,c(3,5,6,7,8)], tindex)
q2.zoo = q2.zoo[tradeintval,]

# merge by 'outer join'
qa = merge(q1.zoo, q2.zoo, all=T, suffixes=c('q1', 'q2'))
# fill gap with latest updates
qa2 = na.locf(qa, na.rm=T) # fill gap with last quotation update

opensprd = qa2$buyprice1.q2 - qa2$sellprice1.q1
clossprd = qa2$sellprice1.q2 - qa2$buyprice1.q1
midsprd = (opensprd+clossprd)/2
badiff = clossprd-opensprd
sprd = cbind(opensprd, clossprd, midsprd, badiff)
# remove the NAs in the first line for the extreme case
sprd = na.locf(sprd, na.rm=T)

# plot sprd by days
# with stats: mean/median, sd, skewness, kurtosis, qqnorm, adf.test, hlife
# also with above stats for the first xx minutes.
# Q: if daiyly spread mean is a good equilibrium point, how much time does it
#    need to converge starting from opening?

sprdstats <- function(sprd)
{
  c(mean(sprd), median(sprd), sd(sprd), 
    skewness(sprd), kurtosis(sprd), adf.test(sprd)$p.value,
    ouhlife(sprd))
}

dayidx = as.POSIXct(trunc(index(sprd), 'days'))
days = unique(dayidx)

# aggregate by day, for several daily statistics.
aggstats = aggregate(sprd$midsprd, by=dayidx, sprdstats)
names(aggstats) = c('mean', 'median', 'sd', 'skewness', 'kurtosis',
                    'adf.pvalue','hlife')

sprdfn = paste('sprd', qfn.base, 'pdf', sep='.')
pdf(sprdfn, width=17.55, height=11.07)

plot(aggstats, type='o', pch='+', main=paste('sprd for', qfn.base))

for (i in 1:length(days))
{
  d = days[i]
  idx = which(dayidx == d)
  # daily spread
  dsprd = sprd[idx,]
  plot(dsprd, type='s', 
       screens=c(1,1,2,3), col=c(rgb(1,0,0,0.5), rgb(0,0,1,0.5), rgb(0,0,0,0.5), 'black'),
       main=paste('sprd for', format(d)))
  qqnorm(dsprd$midsprd, main= paste('qqnorm for', format(d)))
  qqline(dsprd$midsprd)
}
dev.off()
