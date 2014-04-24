library(zoo)
library(ggplot2)
library(PerformanceAnalytics)

source('sbeta.r')

qfn = 'citic.level1.csv'
#qfn = 'benchmark.csv'
#qfn = 'hs300sec.csv'
pzoo = read.zoo(qfn, header=T, sep=',', 
                colClasses=c('character',rep('numeric',29)))
#pzoo = window(pzoo, start='2011-1-1')
pmat = as.matrix(pzoo)

bmfn = 'benchmark.csv'
bmzoo = read.zoo(bmfn, header=T, sep=',', 
                colClasses=c('character',rep('numeric',6)))
bmzoo = bmzoo[,4]
#bmzoo = window(bmzoo, start='2011-1-1')
bmmat = as.matrix(bmzoo)

# build weights
wt = eqweight(NROW(pmat), NCOL(pmat))

# rebalance points
rbpoint = seq(10, NROW(pmat), by=21)

# wealth path
wealth = rebalance(pmat, wt, rbpoint)
wzoo = zoo(wealth, index(pzoo))

# rebase benchmark index
allzoo = cbind(wzoo, bmzoo, all=FALSE)
allzoo = rebase(allzoo)

# compare performance

#ggplot(as.data.frame(allzoo), )
autoplot(allzoo, facet=NULL) + aes(linetype=Series)
plot(log(allzoo$wzoo/allzoo$bmzoo), type='l')

# compare return-risk measures
