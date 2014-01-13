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

#stock.zoo
#index.zoo

stock.zoo = zoo(1:20, as.Date("2003-02-01")+1:20)
lagret = exp(diff(log(stock.zoo), lag=lagu))-1
holdret = exp(diff(log(stock.zoo), lag=-holdu))-1
# select most xxx stocks (columns in zoo)