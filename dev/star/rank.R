library(zoo)

# input: a benchmark quote record, a set of stock/index records for testing.

# params
nstock = 50
lagu = 20
holdu = 20

# backtest idea:
# 1. for each day, sort lag-day stock returns
# 2. select most underperformed / overperformed stock with equal weights
# 3. hold the stocks for hold days, compare net gain against an index's performance

citicq.fn = 'citic.level1.csv'
citicq.zoo = read.zoo(citicq.fn, header=T, sep=',', colClasses=c('character',rep(c('numeric','NULL'),29)))

hs300q.fn = 'hs300.csv'
hs300q.zoo = read.zoo(hs300q.fn, header=T, sep=',', colClasses=c('character',rep(c('numeric','NULL'),1)))

all.zoo = merge(hs300q.zoo, citicq.zoo, all=FALSE)

lagret = exp(diff(log(all.zoo), lag=lagu))-1
holdret = exp(diff(log(all.zoo), lag=-holdu))-1

# relative return with first column (hs300)
rellagret = lagret - lagret[,1]
rellagret = rellagret[,-1]
relholdret = holdret - holdret[,1]
relholdret = relholdret[,-1]

tmp = merge(rellagret, relholdret, all=FALSE)