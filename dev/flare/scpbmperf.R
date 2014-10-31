# test the benchmark performance for reversal-trade. The benchmark is to long/short on every
# tick, and use the same exit strategy as reversal-trade.

# loops: entry/exit params, trading ticks

library(PerformanceAnalytics)
options(digits.secs=3)

args = commandArgs(T)

qhistfn = 'xxx'

trdrptfn = 'zzz.rpt'

if(length(args) >= 2)
{
  qhistfn = args[1]
  trdrptfn = args[2]
}

datestr = unlist(strsplit(qhistfn, split='.', fixed=T))[2]
visdate = strptime(datestr, format="%Y-%m-%d")

qhist = read.csv(qhistfn, header=T)

paramset = data.frame(maxloss=-5, maxdd=-5, maxprofit=10)

possibleNROW = NROW(qhist) * NROW(paramset)

trdrpt = data.frame(
  maxlossparam = numeric(possibleNROW),
  maxddparam = numeric(possibleNROW),
  maxprofitparam = numeric(possibleNROW),
  date = character(possibleNROW),
  ctick = numeric(possibleNROW),
  cprice = numeric(possibleNROW),
  testtdir = numeric(possibleNROW),
  testearn = numeric(possibleNROW),
  stoptick = numeric(possibleNROW),
  stoppnl = numeric(possibleNROW),
  stopby = character(possibleNROW),
  validrow = numeric(possibleNROW)
)

starttic = 9*3600 + 30*60
endtic = 11*3600 + 45*60

print(possibleNROW)

for(i in 1:NROW(qhist))
{
  if(i %% 50 == 0) print(i)
  if((qhist$tic[i]>starttic) & (qhist$tic[i]<endtic))
  {
    # NOTE: just test long
    # prepare quote and pnl
    qline = qhist[i,]
    
    ctick = qline$tic
    cprice = qline$ask1
    tdir = -1
    earn = -0.2
    tmp1 = i
    
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
      
      stoploss.tick = which(pnl.pt<(maxloss))[1]
      stopprofitbymax.tick = which(pnl.pt>maxprofit)[1]
      stopprofitbydd.tick = which(dd.pt<(maxdd) & pnl.pt>0)[1]
      last.tick = NROW(pnl.pt)
      
      allstops = c(stoploss.tick, stopprofitbymax.tick, stopprofitbydd.tick, last.tick)
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
      
      rindex = (i-1)*NROW(paramset) + j
      
      trdrpt$maxlossparam[rindex] = maxloss
      trdrpt$maxddparam[rindex] = maxdd
      trdrpt$maxprofitparam[rindex] = maxprofit
      trdrpt$date[rindex] = datestr
      trdrpt$ctick[rindex] = ctick
      trdrpt$cprice[rindex] = cprice
      trdrpt$testtdir[rindex] = tdir
      trdrpt$testearn[rindex] = earn
      trdrpt$stoptick[rindex] = stoptick
      trdrpt$stoppnl[rindex] = stoppnl
      trdrpt$stopby[rindex] = stopby
      trdrpt$validrow[rindex] = 1
    }
  }
}
write.csv(trdrpt, trdrptfn, row.names=F)
