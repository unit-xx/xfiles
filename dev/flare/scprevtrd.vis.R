library(PerformanceAnalytics)
options(digits.secs=3)

args = commandArgs(T)

qhistfn = 'xxx'
thistfn = 'yyy'

datestr = unlist(strsplit(qhistfn, split='.', fixed=T))[2]
visdate = strptime(datestr, format="%Y-%m-%d")

tvisfn = 'xxx.pdf'

if(length(args) >= 3)
{
  qhistfn = args[1]
  thistfn = args[2]
  tvisfn = args[3]
}

qhist = read.csv(qhistfn, header=T)
thist = read.csv(thistfn, header=T)

for(i in 1:NROW(thist))
{
  # visual only force closed trades
  tline = thist[i,]
  if(tline$force==1)
  {
    ctick = tline$ctime
    tdir = tline$tdir
    tmp1 = which(qhist$tic==ctick)
    
    if(tdir==-1)
    {
      pnl = qhist$bid1[(tmp1+1):NROW(qhist)] - qhist$ask1[tmp1]
    } else
    {
      pnl = -qhist$ask1[(tmp1+1):NROW(qhist)] + qhist$bid1[tmp1]
    }
    
    pnlts = visdate+qhist$tic[(tmp1+1):NROW(qhist)]
    pnl.xts = xts(pnl, order.by=pnlts)
  }
}


# get PnL trace

# get drawdown trace

# 