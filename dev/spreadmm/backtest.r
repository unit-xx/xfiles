library(chron)
library(zoo)
library(tseries)
library(moments)

sprdbt <- function(legq, beta, signal)#, margin, cost)
{
# given a series of legs quotations, and its weights-in-share (beta), backtest
# trading performance using signal. margin/cost(vector) is given for each leg,
# whose lengths are as same as the column numbers of legq.

# @legq: zoo objest, legs quotations
# @beta: vector, weights-in-share
# @signal: zoo object, two columns. C1 for open/close,
#          -1 for short, +1 for long
#          +1 after a -1 means short one copies then close.
#          C2 for trading ID, or label, etc.
#          open/close should be paired, i.e., no partial close.
# @margin: vector
# @cost: vector

# ALGO: aggregate on trade label. for each trade, calculate:
# required capital, income, tcost, profit, max drawdown.
  
  # TODO: improve the expression
  sprd = rollapply(legq, 1, FUN=function(x,beta){sum(x*beta)}, beta, by.column=F)
  tid = unique(signal[,2])
  tperf = data.frame(stringsAsFactors=F)
  
  for(t in tid)
  {
    o = which(signal[,2]==t)
    s= signal[o,]
    if(sum(s[,1])!=0 | NROW(s)!=2)
    # must contain two ops: open&close, trading shares must equal
    {
      warning(paste('trading signal error for tid', t))
      next
    }
    trdtime = index(s)
    # TODO: improve the expression, how?
    osprd = as.numeric(sprd[trdtime[1],])
    csprd = as.numeric(sprd[trdtime[2],])
    gain = as.numeric(s[1,][,1])*(csprd-osprd)
    
    #print(c(tid, osprd, csprd, gain))
    
    # TODO: improve the expression, do.call?
    tperf = rbind(tperf, as.data.frame(list(tid=tid, gain=gain)))
  }
  tperf
}
