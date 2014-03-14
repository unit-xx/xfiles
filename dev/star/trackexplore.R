# explore index tracking by `manually exploring'.

library(zoo)

qfn = 'hs300set.csv'
#qfn = 'swsyset.csv'
startdate = as.Date('')
enddate = as.Date('')

quoteraw = read.zoo(qfn, sep=',', header=T, FUN=as.Date)
quote = quoteraw[500:NROW(quoteraw)]

plot(quote)

lmrst = lm(X000300.SH~X000010.SH+X150019.SZ, data=quote)
plot(zoo(lmrst$residuals, index(quote))[1:NROW(quote)], type='l')

qlog = log(quote)
difqlog = qlog - qlog[,1]
lmrst2 = lm(X000300.SH~X000010.SH+X150019.SZ, data=qlog)
plot(zoo(lmrst2$residuals, index(quote))[1:NROW(quote)], type='l')
