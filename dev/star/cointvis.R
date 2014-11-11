# for a index and a set of stocks, select most cointegrated stocks and see if the portfolio
# is cointegrated with the index in out-of-sample periods. This is done in a moving window
# fashion.

library(tseries)

param = list()
param$tag = 'pp'
param$winsize = 500 # about every 2 years
param$step = 120 # about every half year
param$maxpvalue = 0.1
param$oossize = 500 # out of sample period

idxfn = 'hs300.csv'
stkfn = 'zz800.csv'

idxq = read.csv(idxfn, header=T, stringsAsFactors=F)
stkq = read.csv(stkfn, header=T, stringsAsFactors=F)

# for a fixed period, i is the starting time.
for(i in seq(1, NROW(stkq)-param$winsize, param$step))
{
  # cointegration test and stock selection on in-sample-quote
  stkisq = stkq[i:(i+param$winsize)]
  stkselector = rep(0, NCOL(stkq))
  idxisq = stkq[i:(i+param$winsize), 2]
  # for every stock, column 1 is date which is skipped
  for(j in 2:NCOL(stkq))
  {
    stkisqA = stkisq[,j]
    lmrst = lm(idxisq~stkisqA)
    pvalue = adf.test(residuals(lmrst), alternative="stationary")$p.value
    stkselector[j] = ifelse((pvalue<param$maxpvalue), 1, 0)
  }
  
  # check cointegration on out of sample quote
  # eq-weight?
}