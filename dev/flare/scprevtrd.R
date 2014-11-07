library(PerformanceAnalytics)
options(digits.secs=3)

args = commandArgs(T)

qhistfn = 'xxx'
thistfn = 'yyy'

trdrptfn = 'zzz.rpt'

if(length(args) >= 3)
{
  qhistfn = args[1]
  thistfn = args[2]
  trdrptfn = args[3]
}

datestr = unlist(strsplit(qhistfn, split='.', fixed=T))[2]
visdate = strptime(datestr, format="%Y-%m-%d")

qhist = read.csv(qhistfn, header=T)
thist = read.csv(thistfn, header=T)

# tag = 'p1
maxloss = seq(-5, -5)
maxdd = seq(-5, -5)
maxprofit = seq(1, 30)

# tag = 'p2
#maxloss = seq(-1, -1)
#maxdd = seq(-1, -1)
#maxprofit = seq(1, 30)

paramset = expand.grid(maxloss=maxloss, maxdd=maxdd, maxprofit=maxprofit)

trdrpt = data.frame()

for(i in 1:NROW(thist))
{
  # visual only force closed trades
  tline = thist[i,]
  if(tline$force==1)
  {
    ctick = tline$ctime
    cprice = tline$cprice
    tdir = tline$tdir
    earn = tline$earn
    tmp1 = which(qhist$tic==ctick)
    
    if(tdir==-1)
    # 'reversed trade', if the test order is short, then we long on trend.
    {
      pnl = (qhist$bid1[(tmp1+1):NROW(qhist)] - cprice)/cprice
    } else
    {
      pnl = (-qhist$ask1[(tmp1+1):NROW(qhist)] + cprice)/cprice
    }
    pnl = c(0, pnl)
    
    pnlts = visdate+qhist$tic[(tmp1):NROW(qhist)]
    pnl.xts = xts(pnl, order.by=pnlts)
    pnl.pt = pnl.xts * cprice
    
    #print(is(pnlts))
    dd = Drawdowns(diff(log(pnl.xts+1)))
    dd.pt = dd * cprice
    
    # do trade
    for(j in 1:NROW(paramset))
    {
      maxloss = paramset$maxloss[j]
      maxdd = paramset$maxdd[j]
      maxprofit = paramset$maxprofit[j]
      
      stoploss.tic = which(pnl.pt<(maxloss))[1]
      stopprofitbymax.tick = which(pnl.pt>maxprofit)[1]
      stopprofitbydd.tick = which(dd.pt<(maxdd) & pnl.pt>0)[1]
      last.tick = NROW(pnl.pt)
      
      allstops = c(stoploss.tic, stopprofitbymax.tick, stopprofitbydd.tick, last.tick)
      stoporder = order(allstops)
      if(stoporder[1]==1)
      {
        stopby = 'stoploss'
        
      }else if(stoporder[1]==2)
      {
        stopby = 'hitmax'
        
      }else if(stoporder[1]==3)
      {
        stopby = 'hitdd'
        
      }else if(stoporder[1]==4)
      {
        stopby = 'lastsecond'
        
      }
      stoptick = allstops[stoporder[1]]
      stoppnl = pnl.pt[stoptick]
      
      rptline = data.frame(maxlossparam=maxloss, maxddparam=maxdd, maxprofitparam=maxprofit,
                           date=datestr, ctick=ctick, cprice=cprice, testtdir=tdir,
                           testearn=earn,
                           stoptick=stoptick, stoppnl=stoppnl,
                           stopby=stopby
                           )
      if(NROW(trdrpt)==0)
      {
        trdrpt = rptline
      } else
      {
        trdrpt = rbind(trdrpt, rptline)
      }
    }
  }
  write.csv(trdrpt, trdrptfn, row.names=F)
}
