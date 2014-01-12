# 1. how average correlation changes over time.
# 2. visualize correlation on some time spots.

library(zoo)
library(tseries)

fn = 'citic.level1.csv'
retdata = read.zoo(fn, header=T, sep=',', colClasses=c('character',rep(c('NULL','numeric'),29)))

winsize = 120
step = 20

firstend = winsize
endtick = seq(firstend, NROW(retdata), step)
startick = endtick - winsize + 1
avgcor.zoo = zoo(0, index(retdata)[endtick])
avgsd.zoo = zoo(0, index(retdata)[endtick])
avgcoint.zoo = zoo(0, index(retdata)[endtick])

for(i in 1:length(startick))
{
  subret = retdata[startick[i]:endtick[i],]
  cormat = cor(subret)
  cdim = NROW(cormat)
  avgcor = (sum(cormat) - cdim)/cdim/(cdim-1)
  avgcor.zoo[i] = avgcor
  
  covmat = cov(subret)
  avgsd = mean(diag(covmat))
  avgsd.zoo[i] = avgsd
}
plot(avgcor.zoo, main='avgcor')
plot(avgsd.zoo, main='avgvar')
plot(avgsd.zoo*sqrt(1-avgcor.zoo**2), main='avgcor*avgvar')
