# a simple dual momentum strategy
# long a stock/index when 1) it is top N by return of previous k months 
# 2) its return of previous k months is better than cash account

library(zoo)

# input: 
# pzoo, price series by column
# N, top N in momentum
# k1, k2, lookback from k1 to k2 days 
# step, rebalance every step days
# r, rate of cash account

# read pzoo

qfn = 'citic.level1.csv'
pzoo = read.zoo(qfn, header=T, sep=',', 
                colClasses=c('character',rep('numeric',29)))



# back test and generate trading traces

# at predefined rebalance days
# - close all previous positions, calc return series
# - select targets to buy
# - rebalance postions as equal weight

# performance summary