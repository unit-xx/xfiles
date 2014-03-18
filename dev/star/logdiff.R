library(zoo)
library(glmnet)

qfn = 'hs300stk.csv'
startdate = as.Date('')
enddate = as.Date('')

zero2na <- function(x)
{
  ind = which(x==0)
  replace(x, ind, NA)
}

nacount <- function(x)
{
  return(sum(is.na(x)))
}

quoteraw = read.zoo(qfn, sep=',', header=T, FUN=as.Date)
# replace 0 with NA
quote = apply(quoteraw, 2, zero2na)
# count how much NA is each series
nacnt = apply(quote, 2, nacount)
naratio = nacnt/NROW(quote)
# remove tickers with too much NAs
quote = quote[,which(naratio<0.05)]

quote = zoo(quote, index(quoteraw))
qlog = log(quote)
qlogdiff = qlog - qlog[,1]

pdf(sprintf('%s.logdiff.pdf', qfn), width=17.55, height=11.07)
for(j in 1:NCOL(qlogdiff))
{
  plot(qlogdiff[,j], plot.type='multiple', type='l', main=names(qlogdiff)[j])
}
dev.off()

numstk = 100 # NCOL(quote) - 1

# normal regression
fml = as.formula(sprintf('X000300.SH~%s', paste(names(qlogdiff)[2:(numstk+1)], collapse='+')))
lmrst = lm(fml, data=quote)
plot(lmrst$residuals, type='l')

# lasso regression using glmnet
qnona = na.omit(quote[,1:(numstk+1)])
qnona = (as.matrix(qnona))

lmlasso = glmnet(qnona[,2:(numstk+1)], t(qnona[,1]), lambda=exp(seq(-8,8,0.1)))
plot(lmlasso, xvar='lambda')

fity = predict(lmlasso, newx=qnona[,2:(numstk+1)], s=exp(-1))
resid = fity - qnona[,1]
plot(resid, type='l')
# coef(lmlasso, s=exp(-4))

cvlasso = cv.glmnet(qnona[,2:(numstk+1)], t(qnona[,1]), lambda=exp(seq(-8,8,0.1)))
plot(cvlasso)

# lasso regress by segments
segstart = 200
segend = 800
qseg = qnona[seq(segstart,segend),]
lmlasso = glmnet(qseg[,2:(numstk+1)], t(qseg[,1]), lambda=exp(seq(-16,16,0.1)))
plot(lmlasso, xvar='lambda')

cvlasso = cv.glmnet(qseg[,2:(numstk+1)], t(qseg[,1]), lambda=exp(seq(-16,16,0.1)))
plot(cvlasso)

#fity = predict(lmlasso, newx=qnona[,2:(numstk+1)], s=exp(-1))
loglmbda = -1
fity = predict(lmlasso, newx=qnona[,2:(numstk+1)], s=exp(loglmbda))
resid = qnona[,1] - fity
plot(resid, type='l', main=sprintf('loglambda=%.2f',loglmbda))
abline(v=c(segstart, segend))
#plot(qnona[,1], type='l')


