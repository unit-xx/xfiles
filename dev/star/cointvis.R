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

# NOTE: check they share the same date
idxq = read.csv(idxfn, header=T, stringsAsFactors=F)
stkq = read.csv(stkfn, header=T, stringsAsFactors=F)
print(which(!(stkq[,1]==idxq[,1])))

# replace 0 in stkq with latest observation
stkq[stkq==0] = NA
stkq = na.locf(stkq)

datestr = idxq[,1]
idxq = idxq[,-1]
stkq = stkq[,-1]

# for a fixed period, i is the starting time.
for(i in seq(1, NROW(stkq)-param$winsize, param$step))
{
  # cointegration test and stock selection on in-sample-quote
  stkisq = stkq[i:(i+param$winsize),]
  stkselector = rep(0, NCOL(stkq))
  idxisq = idxq[i:(i+param$winsize)]
  idxisq.log = log(idxisq)
  # for every stock, column 1 is date which is skipped
  for(j in 1:NCOL(stkq))
  {
    stkisqA = stkisq[,j]
    if(is.na(stkisqA[1]))
    {
      stkselector[j] = 1
    } else
    {
      retdiff = log(stkisqA) - idxisq.log
      pvalue = adf.test(retdiff, alternative="stationary")$p.value
      stkselector[j] = ifelse((pvalue<param$maxpvalue), pvalue, 1)
    }
  }
  
  # print in-sample-return portfolio
  
  # check cointegration on out of sample quote
}