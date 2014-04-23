library(zoo)

rebalance <- function(pmat, wt, rbpoint, cashinit=100)
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

qfn = 'citic.level1.csv'
pzoo = read.zoo(qfn, header=T, sep=',', 
                colClasses=c('character',rep('numeric',29)))
pmat = as.matrix(pzoo)

wt = 
rbpoint = 