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

ptfeqwret <- function(stkq)
{
  stkq.eqw = sweep(stkq, 2, unlist(stkq[1,]), `/`)
  ptfosq = apply(stkq.eqw, 1, sum) / NCOL(stkq.eqw)
  return(ptfosq)
}

pdf('cointvis.pdf', width=17.55, height=11.07)

# for a fixed period, i is the starting time.
for(i in seq(1, NROW(stkq)-param$winsize-param$oossize, param$step))
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
  
  stkosq = stkq[(i+param$winsize):(i+param$winsize+param$oossize),which(stkselector!=1)]
  idxosq = idxq[(i+param$winsize):(i+param$winsize+param$oossize)]

  ptfisq = ptfeqwret(stkisq[,which(stkselector!=1)])
  idxisq2 = idxisq / idxisq[1]
  iretdiff = log(ptfisq) - log(idxisq2)
  ipvalue = adf.test(iretdiff, alternative="stationary")$p.value
  plot(iretdiff, type='l', main=sprintf('insample %d, from=%s to=%s pvalue=%.3f', length(which(stkselector!=1)), datestr[i], datestr[i+param$winsize], ipvalue))

  ptfosq = ptfeqwret(stkosq)
  idxosq2 = idxosq / idxosq[1]
  oretdiff = log(ptfosq) - log(idxosq2)
  opvalue = adf.test(oretdiff, alternative="stationary")$p.value
  plot(oretdiff, type='l', main=sprintf('outsample %d, from=%s to=%s pvalue=%.3f', length(which(stkselector!=1)), datestr[i+param$winsize], datestr[i+param$winsize+param$oossize], opvalue))
}

dev.off()