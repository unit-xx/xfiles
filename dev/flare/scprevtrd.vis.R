library(PerformanceAnalytics)
library(xts)
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

for(i in 1:NROW(thist))
{
  # visual only force closed trades
  tline = thist[i,]
  if(tline$force==1)
  {
    ctick = tline$ctime
    cprice = tline$cprice
    tdir = tline$tdir
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
    
    plot(pnl.pt, main=sprintf('PNL %d/%d trade in %s', i, NROW(thist), datestr))
    plot(dd.pt, main=sprintf('DD %d/%d trade in %s', i, NROW(thist), datestr))
  }
}

dev.off()
# get PnL trace

# get drawdown trace

# 