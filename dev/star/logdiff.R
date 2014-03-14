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

quoteraw = read.zoo(qfn, sep=',', header=T, FUN=as.Date)
quote = apply(quoteraw, 2, zero2na)
quote = zoo(quote, index(quoteraw))
qlog = log(quote)
qlogdiff = qlog - qlog[,1]

pdf(sprintf('%s.logdiff.pdf', qfn), width=17.55, height=11.07)
for(j in 1:NCOL(qlogdiff))
{
  plot(qlogdiff[,j], plot.type='multiple', type='l', main=names(qlogdiff)[j])
}
dev.off()

numstk = 2

# normal regression
fml = as.formula(sprintf('X000300.SH~%s', paste(names(qlogdiff)[2:(numstk+1)], collapse='+')))
lmrst = lm(fml, data=quote)
plot(lmrst$residuals, type='l')

# lasso regression using glmnet
qnona = na.omit(quote[,1:(numstk+1)])
qnona = (as.matrix(qnona))
cvlasso = cv.glmnet(qnona[,2:(numstk+1)], t(qnona[,1]))
plot(cvlasso)

lmlasso = glmnet(qnona[2:(numstk+1),], qnona[1,])