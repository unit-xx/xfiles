# moving cointegration coefficient.

library(zoo)
library(tseries)

#subidxq.fn = 'citic.level1.csv' 29
subidxq.fn = 'subhs300.csv'
subidxq.zoo = read.zoo(subidxq.fn, header=T, sep=',', colClasses=c('character',rep(c('numeric','NULL'),13)))
irange = which(index(subidxq.zoo)>as.Date('2005-01-01'))
subidxq.zoo = subidxq.zoo[irange,]

hs300q.fn = 'hs300.csv'
hs300q.zoo = read.zoo(hs300q.fn, header=T, sep=',', colClasses=c('character',rep(c('numeric','NULL'),1)))

all.zoo = merge(hs300q.zoo, subidxq.zoo, all=FALSE)

#hs300q.zoo = all.zoo[,1]
#subidxq.zoo = all.zoo[,-1]

coint1vall <- function(q1)
{
  q2 = as.data.frame(q1)
  ret = rep(0, NCOL(q2)-1)
  midx = q2[,1]
  for(i in 2:NCOL(q2))
  {
    subidx = q2[,i]
    lmrst = lm(subidx~midx)
    # TODO: adf.test consider trends?
    pvalue = adf.test(residuals(lmrst), alternative="stationary")$p.value
    ret[i-1] = pvalue
  }
  return(ret)
}

wsize = 160
step = 5
coint.all = rollapplyr(all.zoo, wsize, FUN=coint1vall, by=step,  by.column=F)