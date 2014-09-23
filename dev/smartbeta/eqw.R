# another equal-weight strategy implementation

# input: series of tickers quotes
# output: equal-weight (timely etc.) adjusted index of all the tickers.

con = gzcon(file('./sit.gz', 'rb'))
source(con)
close(con)

qfn = 'xxx.csv'

quotes = read.zoo(qfn, sep=',', header=T)

capital = 1000000

data = new.env()
data$prices = coredata(quotes)
data$dates = index(quotes)
data$symbolnames = names(quotes)
data$weight = req(NA, NROW(quotes))

# prepare adjustment points

adjpoint = timely.adjust(data$dates)
data$weight[adjpoint] = 1 / length(data$symbolnames)
data$weight[] = data$weight * capital / data$prices

model = list()
model$eqw = bt.run(data, trade.summary = T, do.lag = 0, type='share')



# 