library(quantmod)

con = gzcon(file('./sit.gz', 'rb'))
source(con)
close(con)

data = new.env()
getSymbols('SPY', env=data)

chartSeries(data$SPY)

bt.prep(data)

model = list()

capital = 100000

data$weight[] = 0.5
model$bys = bt.run.share(data, trade.summary = T, do.lag = 0)

data$weight[] = NA
data$weight[endpoints(data$weight)] = 0.5
data$weight[] = data$weight * capital / data$prices
model$monthlyreb = bt.run(data, trade.summary = T, do.lag = 0, type='share')

strategy.performance.snapshoot(model$bys, T)

data$weight[] = 0.5
model$byw = bt.run(data, trade.summary = T, type='weight', do.lag = 0)
strategy.performance.snapshoot(model$byw, T)

strategy.performance.snapshoot(model, T)

