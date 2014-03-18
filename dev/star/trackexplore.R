# explore index tracking by `manually exploring'.

library(zoo)

qfn = 'hs300set.csv'
#qfn = 'swsyset.csv'
startdate = as.Date('')
enddate = as.Date('')

quoteraw = read.zoo(qfn, sep=',', header=T, FUN=as.Date)
quote = quoteraw[500:NROW(quoteraw)]

plot(quote)

# plain regression
lmrst = lm(X000300.SH~X000010.SH+X150019.SZ, data=quote[seq(segstart,segend),])
plot(as.vector(quote[,1])-predict(lmrst, newx=quote[,c(2,5)]), type='l')
abline(v=c(segstart, segend))

qlog = log(quote)
difqlog = qlog - qlog[,1]
lmrst2 = lm(X000300.SH~X000010.SH+X150019.SZ, data=qlog)
plot(zoo(lmrst2$residuals, index(quote))[1:NROW(quote)], type='l')

# lasso regression
segstart = 200
segend = 600
qseg = qmat[seq(segstart,segend),]
lmlasso = glmnet(qseg[,c(2,5)], t(qseg[,1]), lambda=exp(seq(-16,16,0.1)))
plot(lmlasso, xvar='lambda')

cvlasso = cv.glmnet(qseg[,c(2,5)], t(qseg[,1]), lambda=exp(seq(-16,16,0.1)))
plot(cvlasso)

#fity = predict(lmlasso, newx=qnona[,2:(numstk+1)], s=exp(-1))
loglmbda = -0
fity = predict(lmlasso, newx=qmat[,c(2,5)], s=exp(loglmbda))
resid = qmat[,1] - fity
plot(resid, type='l', main=sprintf('loglambda=%.2f',loglmbda))
abline(v=c(segstart, segend))
#plot(qnona[,1], type='l')
