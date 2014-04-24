# a simple dual momentum strategy
# long a stock/index when 1) it is top N by return of previous k months 
# 2) its return of previous k months is better than cash account

library(zoo)
library(PerformanceAnalytics)

# input: 
# pzoo, price series by column
# N, top N in momentum
# k1, k2, lookback from k1 to k2 days 
# step, rebalance every step days
# r, rate of cash account

topn = 5
k1 = 200
k2 = 1
rbstep = 21
rf = 0.03

# read pzoo

qfn = 'citic.level1.csv'
pzoo = read.zoo(qfn, header=T, sep=',', 
                colClasses=c('character',rep(c('numeric','NULL'),29)))
pmat = as.matrix(pzoo)

bmfn = 'benchmark.csv'
bmzoo = read.zoo(bmfn, header=T, sep=',', 
               colClasses=c('character',rep('numeric',5)))
bmzoo[which(bmzoo==0)] = NA

# rebalance points

rbday.prev = 1
rbday = k1 + 1
sharevec = rep(0, NCOL(pzoo))
wealth = rep(0, NROW(pzoo))
cash = 100

repeat
{
  #browser()

  if(rbday > NROW(pmat))
  {
    # calc returns from last rebalacne day to the end of day of pmat
    pseg = pmat[rbday.prev:NROW(pmat),]
    wseg = pseg %*% sharevec + cash
    wealth[rbday.prev:NROW(pmat)] = wseg

    break
  }
  
  print(rbday)
  
  # calc wealth between rbday and previous rbday
  
  pseg = pmat[rbday.prev:rbday,]
  wseg = pseg %*% sharevec + cash
  wealth[rbday.prev:rbday] = wseg
  
  # sell all existing stocks
  
  cash = wealth[rbday]
  sharevec = rep(0, NCOL(pzoo))

  # re-select topN dual momentum 
  
  plookback1 = pmat[(rbday-k1),]
  plookback2 = pmat[(rbday-k2),]
  # annualize return in lookback periods
  retlb = (plookback2 / plookback1 - 1) / (k1 - k2) * 252
  
  # TODO: add absolute momentum
  topnstock = order(retlb, decreasing=T)[1:topn]
  absmmtstock = which(retlb >= rf)
  targetstock = intersect(topnstock, absmmtstock)
  
  # buy new stocks
  
  if(length(targetstock) > 0)
  {
    cashvec = rep(0, NCOL(pzoo))
    cashvec[targetstock] = cash / length(targetstock)
    sharevec = cashvec / pmat[rbday,]
    cash = 0
  }

  # step to next rebalance day
  
  rbday.prev = rbday
  rbday = rbday + rbstep
}

wzoo = zoo(wealth, index(pzoo))
wzoo = cbind(wzoo, bmzoo)


# back test and generate trading traces

# at predefined rebalance days
# - close all previous positions, calc return series
# - select targets to buy
# - rebalance postions as equal weight

# performance summary