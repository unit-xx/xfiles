library(PerformanceAnalytics)
options(digits.secs=3)

args = commandArgs(T)

qhistfn = 'xxx'
thistfn = 'yyy'

tvisfn = 'xxx.pdf'

if(length(args) >= 3)
{
  qhistfn = args[1]
  thistfn = args[2]
  tvisfn = args[3]
}

datestr = unlist(strsplit(qhistfn, split='.', fixed=T))[2]
visdate = strptime(datestr, format="%Y-%m-%d")

qhist = read.csv(qhistfn, header=T)
thist = read.csv(thistfn, header=T)

pdf(tvisfn, width=17.55, height=11.07)

allpnl = numeric(0)
alltestearn = numeric(0)

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
    
    stoploss.tic = which(pnl.pt<(-5))[1]
    stopprofitbymax.tick = which(pnl.pt>10)[1]
    stopprofitbydd.tick = which(dd.pt<(-5) & pnl.pt>0)[1]
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
    
    
    # plot pnl and dd, with stop tick/type and pnl
    plot(pnl.pt, main=sprintf('PNL (%d/%d trade in %s, testearn=%.2f)', i, NROW(thist), datestr, earn))
    abline(v = index(pnl.pt)[stoptick], col="red", lty="dotted")
    text(index(pnl.pt)[stoptick], 0, labels=stopby)
    
    plot(dd.pt, main=sprintf('DD (%d/%d trade in %s, testearn=%.2f)', i, NROW(thist), datestr, earn))
    abline(v = index(pnl.pt)[stoptick], col="red", lty="dotted")
    par(xpd=TRUE)
    text(index(pnl.pt)[stoptick], 0, labels=stopby, pos=3)
    
    print(stoppnl)
    
    allpnl = c(allpnl, stoppnl)
    alltestearn = c(alltestearn, earn)
  }
}
print(allpnl)
barplot(allpnl, main=sprintf('revtrade profit: Total=%.2f Avg=%.2f', sum(allpnl), mean(allpnl)))
barplot(alltestearn, main=sprintf('testearn: Total=%.2f Avg=%.2f', sum(alltestearn), mean(alltestearn)))

dev.off()
# get PnL trace

# get drawdown trace

# 