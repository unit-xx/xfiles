eqwtrebalance <- function(pmat, wt, rbpoint, cashinit=100)
{
  # back test using price matrix pmat, 
  # with rebalance at time of rbpoint (row numbers), 
  # using weight in wt
  
  # return wealth series
  
  # no transaction fees yet
  
  cash = cashinit
  rbday.prev = 1
  sharevec = rep(0, NCOL(pzoo))
  wealth = rep(0, NROW(pzoo))
  
  for(rbday in rbpoint)
  {
    # calc wealth between rbday and previous rbday
    
    pseg = pmat[rbday.prev:rbday,]
    wseg = pseg %*% sharevec + cash
    wealth[rbday.prev:rbday] = wseg
    
    # re-balance stocks
    
    # sell all existing stocks
    
    cash = wealth[rbday]
    sharevec = rep(0, NCOL(pzoo))
    
    # buy new stocks
    
    wtvec = wt[rbday,]
    cashvec = cash * wtvec
    sharevec = cashvec / pmat[rbday,]
    cash = cash * (1 - sum(wtvec))
    
    # step to next rebalance day
    
    rbday.prev = rbday
  }
  
  if(rbday < NROW(pmat))
  {
    # calc wealth growth in ramaining days
    pseg = pmat[rbday:NROW(pmat),]
    wseg = pseg %*% sharevec + cash
    wealth[rbday:NROW(pmat)] = wseg
  }
  
  return(wealth)
}

dualmmrebalance <- function(pmat, topn, k1, k2, rbstep, rf, cashinit=100)
{
  # N, top N in momentum
  # k1, k2, lookback from k1 to k2 days 
  # step, rebalance every step days
  # r, rate of cash account
  
  rbday.prev = 1
  rbday = k1 + 1
  sharevec = rep(0, NCOL(pzoo))
  wealth = rep(0, NROW(pzoo))
  cash = 100
  
  repeat
  {
    #browser()
    
    if(rbday > NROW(pmat))
    {
      # calc returns from last rebalacne day to the end of day of pmat
      pseg = pmat[rbday.prev:NROW(pmat),]
      wseg = pseg %*% sharevec + cash
      wealth[rbday.prev:NROW(pmat)] = wseg
      
      break
    }
    
    #print(rbday)
    
    # calc wealth between rbday and previous rbday
    
    pseg = pmat[rbday.prev:rbday,]
    wseg = pseg %*% sharevec + cash
    wealth[rbday.prev:rbday] = wseg
    
    # sell all existing stocks
    
    cash = wealth[rbday]
    sharevec = rep(0, NCOL(pzoo))
    
    # re-select topN dual momentum 
    
    plookback1 = pmat[(rbday-k1),]
    plookback2 = pmat[(rbday-k2),]
    # annualize return in lookback periods
    retlb = ((plookback2/plookback1)-1) / (k1-k2) * 252
    
    # TODO: add absolute momentum
    topnstock = order(retlb, decreasing=T)[1:topn]
    absmmtstock = which(retlb >= rf)
    targetstock = intersect(topnstock, absmmtstock)
    
    # buy new stocks
    
    if(length(targetstock) > 0)
    {
      cashvec = rep(0, NCOL(pzoo))
      cashvec[targetstock] = cash / length(targetstock)
      sharevec = cashvec / pmat[rbday,]
      cash = 0
    }
    
    # step to next rebalance day
    
    rbday.prev = rbday
    rbday = rbday + rbstep
  }
  
  return(wealth)
}

rebase <- function(xx, newbase=100)
{
  # rescale series to the same starting base.
  
  # xx is a matrix or data frame, rebase each series (as columns) to newbase
  
  # extend 0 in price series
  xx[which(xx==0)] = NA
  yy = na.fill(xx, 'extend')
  
  yy = sweep(yy, 2, yy[1,], `/`) * newbase
  return(yy)
}

eqweight <- function(nr, nc)
{
  wt = rep(1/nc, nr*nc)
  wt = matrix(wt, nrow=nr)
  return(wt)
}

powerweight <- function(wt.in, pow)
{
  # new weight is proportional to the power of wt.in
  # for example, diversity-weighting is wt.in^pow and rescaled,
  # and inverse volatility weight is wt.in^-1, with wt being volatility.
  
  # it can also be use to normalize rows by set pow=1
  
  wt = wt.in ^ pow
  wt = sweep(wt, 1, apply(wt, 1, sum), '/')
  wt[is.nan(wt)] = 0
  wt[is.na(wt)] = 0
  return(wt)
}

volbysd <- function(pseq)
{
  retseq = log(diff(pseq))
  return(sd(retseq))
}

# rollvol <- function(pseq, volfunc, term)
# {
#   endp = 1:length(pseq)
#   startp = pmax(endp - term + 1, 1)
#   
#   volseq = sapply(startp, 
#          function(startp, endp, seqx, volfunc){return(volfunc(seqx[startp:endp]))},
#          endp, seqx, volfunc)
#   
#   volseq[which(()<term)] = NA
#   return(volseq)
# }

volatility <- function(pseq, term, volfunc)
{
  vol = apply(pseq, 2, rollvol, volfunc, term)
  return(vol)
}