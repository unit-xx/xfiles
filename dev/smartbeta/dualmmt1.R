# a simple dual momentum strategy
# long a stock/index when 1) it is top N by return of previous k months 
# 2) its return of previous k months is better than cash account

library(zoo)
library(PerformanceAnalytics)

source('sbeta.r')

# input: 
# pzoo, price series by column
# N, top N in momentum
# k1, k2, lookback from k1 to k2 days 
# step, rebalance every step days
# r, rate of cash account

topn = 5
k1 = 200
k2 = 20
rbstep = 21
rf = 0.03

# read pzoo

qfn = 'citic.level1.csv'
pzoo = read.zoo(qfn, header=T, sep=',', 
                colClasses=c('character',rep(c('numeric'),29)))
pmat = as.matrix(pzoo)

bmfn = 'benchmark.csv'
bmzoo = read.zoo(bmfn, header=T, sep=',', 
               colClasses=c('character',rep('numeric',6)))
bmzoo = bmzoo[,4]
# bmzoo[which(bmzoo==0)] = NA

# rebalance points

wealthdmm = dualmmrebalance(pmat, topn, k1, k2, rbstep, rf)

wzoo = zoo(wealthdmm, index(pzoo))

allzoo = cbind(wzoo, bmzoo, all=FALSE)
allzoo = rebase(allzoo)

autoplot(allzoo, facet=NULL) + aes(linetype=Series)
plot((allzoo$wzoo/allzoo$bmzoo), type='l')
