# for a index and a set of stocks, select most cointegrated stocks and see if the portfolio
# is cointegrated with the index in out-of-sample periods. This is done in a moving window
# fashion.

# TODO: in/out/inout pvalue correlation, how cointegration set evolve, better cointegration set element selection (subset?)
# TODO: backtest

library(tseries)
library(zoo)

param = list()
param$tag = 'pp'
param$winsize = 500 # about every 2 years
param$step = 120 # about every half year
param$maxpvalue = 0.1
param$oossize = 250 # out of sample period

idxfn = 'hs300.csv'
stkfn = 'zz800.csv'

# NOTE: check they share the same date
idxq = read.csv(idxfn, header=T, stringsAsFactors=F)
stkq = read.csv(stkfn, header=T, stringsAsFactors=F)
print(which(!(stkq[,1]==idxq[,1])))

datestr = idxq[,1]
idxq = idxq[,-1]
stkq = stkq[,-1]

# replace 0 in stkq with latest observation
stkq[stkq==0] = NA
stkq = na.locf(stkq)

ptfeqwret <- function(stkq)
{
  stkq.eqw = log(sweep(stkq, 2, unlist(stkq[1,]), `/`))
  ptfosq = apply(stkq.eqw, 1, sum) / NCOL(stkq.eqw)
  return(ptfosq)
}

pdf('cointvis.pdf', width=17.55, height=11.07)

iptfpvalue = rep(0, length(seq(1, NROW(stkq)-param$winsize-param$oossize, param$step)))
optfpvalue = rep(0, length(iptfpvalue))
ioptfpvalue = rep(0, length(iptfpvalue))
k = 1
# for a fixed period, i is the starting time.
for(i in seq(1, NROW(stkq)-param$winsize-param$oossize, param$step))
{
  # cointegration test and stock selection on in-sample-quote
  stkisq = stkq[i:(i+param$winsize),]
  stkselector = rep(0, NCOL(stkq))
  stkopvalue = rep(0, NCOL(stkq))
  idxisq = idxq[i:(i+param$winsize)]
  idxisq.log = log(idxisq)
  # in sample pvalues
  for(j in 1:NCOL(stkq))
  {
    stkisqA = stkisq[,j]
    if(is.na(stkisqA[1]))
    {
      # 1 for not selected
      stkselector[j] = 1
    } else {
      retdiff = log(stkisqA) - idxisq.log
      pvalue = adf.test(retdiff, alternative="stationary")$p.value
      stkselector[j] = pvalue
    }
  }
  
  stkosq = stkq[(i+param$winsize):(i+param$winsize+param$oossize),]
  idxosq = idxq[(i+param$winsize):(i+param$winsize+param$oossize)]
  idxosq.log = log(idxosq)
  
  # out of sample pvalues
  for(j in 1:NCOL(stkq))
  {
    stkosqA = stkosq[,j]
    if(is.na(stkosqA[1]))
    {
      # 1 for not selected
      stkopvalue[j] = 1
    } else {
      retdiff = log(stkosqA) - idxosq.log
      pvalue = adf.test(retdiff, alternative="stationary")$p.value
      stkopvalue[j] = pvalue
    }
  }
  
  pvalue.cmpset = which(stkselector!=1 & stkopvalue!=1)
  
  plot(stkselector[pvalue.cmpset], stkopvalue[pvalue.cmpset], main='stock opvalue(y) vs ipvalue(x)')

  ptfisq = ptfeqwret(stkisq[,which(stkselector<param$maxpvalue)])
  idxisq2 = idxisq / idxisq[1]
  iretdiff = ptfisq - log(idxisq2)
  ipvalue = adf.test(iretdiff, alternative="stationary")$p.value
  iptfpvalue[k] = ipvalue
  plot(iretdiff, type='l', main=sprintf('insample %d, from=%s to=%s pvalue=%.3f', length(which(stkselector<param$maxpvalue)), datestr[i], datestr[i+param$winsize], ipvalue))

  ptfosq = ptfeqwret(stkosq[,which(stkselector<param$maxpvalue)])
  idxosq2 = idxosq / idxosq[1]
  oretdiff = ptfosq - log(idxosq2)
  opvalue = adf.test(oretdiff, alternative="stationary")$p.value
  optfpvalue[k] = opvalue
  plot(oretdiff, type='l', main=sprintf('outsample %d, from=%s to=%s pvalue=%.3f', length(which(stkselector<param$maxpvalue)), datestr[i+param$winsize], datestr[i+param$winsize+param$oossize], opvalue))

  pdfiosq = ptfeqwret(stkq[i:(i+param$winsize+param$oossize),which(stkselector<param$maxpvalue)])
  idxiosq = idxq[i:(i+param$winsize+param$oossize)]
  idxiosq2 = idxiosq / idxiosq[1]
  ioretdiff = pdfiosq - log(idxiosq2)
  iopvalue = adf.test(ioretdiff, alternative="stationary")$p.value
  ioptfpvalue[k] = iopvalue
  plot(ioretdiff, type='l', main=sprintf('in & outsample %d, from=%s to=%s pvalue=%.3f', length(which(stkselector<param$maxpvalue)), datestr[i], datestr[i+param$winsize+param$oossize], iopvalue))
  abline(v=param$winsize)
  
  k = k + 1
}

plot(iptfpvalue, optfpvalue, main='ptf opvalue(y) vs ipvalue(x)')
plot(iptfpvalue, ioptfpvalue, main='ptf iopvalue(y) vs ipvalue(x)')
plot(optfpvalue, ioptfpvalue, main='ptf iopvalue(y) vs opvalue(x)')

dev.off()
