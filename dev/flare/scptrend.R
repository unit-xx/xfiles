# see also scptrend.py. We follow the trend to buy/sell the contract, and how is the return goes.

library(ggplot2)

args = commandArgs(T)

trendfn = 'xxx'
pdfn = 'xxx.pdf'
stopbtfn = 'xxx.stopbt'

if(length(args) >= 3)
{
  trendfn = args[1]
  pdfn = args[2]
  stopbtfn = args[3]
}

print(trendfn)

trade = read.csv(trendfn, header=F)
odir = trade[,4]
earn = trade[,5]
seequote = trade[,8]
allq = trade[,9:NCOL(trade)]
askq = allq[,seq(1,length.out=NCOL(allq)/2,by=2)]
bidq = allq[,seq(2,length.out=NCOL(allq)/2,by=2)]

ret = data.frame(matrix(NA, nrow=length(odir), ncol=NCOL(askq)-1))
for(i in 1:length(odir))
{
  if(odir[i]==-1)
  {
    oprice = askq[i,1]
    cprice = bidq[i,-1]
    ret[i,] = cprice - oprice
  }
  else{
    oprice = bidq[i,1]
    cprice = askq[i,-1]
    ret[i,] = oprice - cprice
  }
}

pdf(pdfn, width=17.55, height=11.07)

print('plotting returns')
# how each ret series goes
for(i in 1:length(odir))
{
    plot(1:NCOL(ret), ret[i,], type='b', pch='+', xlab='tick', ylab='earn', main=sprintf('odir=%d earn=%.2f seequote=%d', odir[i], earn[i], seequote[i]))    
    abline(h=-1, col='red')
}

# return by close at fixed tick
closetick = seq(1, NCOL(askq)-1)
timelyret = matrix(rep(0.0, length(closetick)*length(odir)), ncol=length(closetick))
# return by stop-loss/win
stoploss.seq = seq(-0.2, max(-4.0, min(ret, na.rm=T)), by=-0.2)
stopwin.seq = seq(0.2, min(4, max(ret, na.rm=T)), by=0.2)
stopret = cbind(expand.grid(stoploss.seq, stopwin.seq, 1:length(odir)), 0.0)
names(stopret) = c('stoploss', 'stopwin', 'index', 'ret')
# return by Oracle: the maximum/minimum possbile return
maxret = rep(0.0, length(odir))
maxpos = rep(0.0, length(odir))
minret = rep(0.0, length(odir))
minpos = rep(0.0, length(odir))

print('timelyret')
# timelyret
for(i in 1:length(odir))
{
  for(t in 1:length(closetick))
  {
    timelyret[i, t] = ifelse(is.na(ret[i,closetick[t]]), 0, ret[i,closetick[t]])
  }
}

timelyret.sum = apply(timelyret, 2, sum)
timelyret.avg = apply(timelyret, 2, mean)
timelyret.sum.seeq = apply(timelyret*seequote, 2, sum)
timelyret.avg.seeq = apply(timelyret*seequote, 2, mean)

# all sample result
plot(timelyret.sum, type='o', pch='+', main=sprintf('sample #=%d, max at %d', length(odir), which.max(timelyret.sum)))
plot(timelyret.avg, type='o', pch='+', main=sprintf('sample #=%d, max at %d', length(odir), which.max(timelyret.avg)))

# only seequote samples
plot(timelyret.sum.seeq, type='o', pch='+', main=sprintf('sum plot only seequote sample #=%d, max at %d', sum(seequote), which.max(timelyret.sum.seeq)))
plot(timelyret.avg.seeq, type='o', pch='+', main=sprintf('avg plot only seequote sample #=%d, max at %d', sum(seequote), which.max(timelyret.avg.seeq)))

print('stoploss/win backtest')
# stop-loss/win return
for(j in 1:NROW(stopret))
{
  stoploss = stopret[j,1]
  stopwin = stopret[j,2]
  i = stopret[j,3]

  stoploss.tick = which(ret[i,]<=stoploss)
  stopwin.tick = which(ret[i,]>=stopwin)
  
  if(length(stoploss.tick)>0)
  {
    if(length(stopwin.tick)>0)
    {
      # which stop-xxx is first encountered?
      if(stopwin.tick[1] < stoploss.tick[1])
      {
        # stopwin encountered first
        stopret[j,4] = stopwin
        #print(stopwin)
      } else
      {
        # stoploss encountered first
        stopret[j,4] = stoploss
        #print(stoploss)
      }
    } else
    {
      # stoploss-ed
      stopret[j,4] = stoploss
      #print(stoploss)
    }
  } else # no stop-loss happens
  {
    if(length(stopwin.tick)>0)
    {
      # stopwin-ed
      stopret[j,4] = stopwin
      #print(stopwin)
    } else
    {
      # close at predefined tick
      stopret[j,4] = ifelse(is.na(ret[i,50]), 0, ret[i,50])
      #print(ifelse(is.na(ret[i,50]), 0, ret[i,50]))
    }
  }
  
  if(j %% 100 == 0)
  {
    print(c(stoploss, stopwin, stopret[j,4], j, NROW(stopret)))
  }
}

stopret$ret.seeq = stopret$ret * seequote[stopret$index]
write.csv(stopret, stopbtfn, row.names=F)

# average return for a fixed (stoploss, stopwin) pair
stopret.avg = aggregate(ret~stoploss+stopwin, data=stopret, FUN=mean)

stopret.avg.seeq = aggregate(ret.seeq~stoploss+stopwin, data=stopret, FUN=mean)

# contour plot
ggplot(stopret.avg.seeq, aes(x=stoploss, y=stopwin, z=ret.seeq)) + stat_contour(aes(colour = ..level..)) + scale_colour_gradient(low = "brown", high = "blue")

# max possible win by Oracle

for(i in 1:length(odir))
{
  maxpos[i] = which.max(ret[i,])
  maxret[i] = max(ret[i,], na.rm=T)
  minpos[i] = which.min(ret[i,])
  minret[i] = min(ret[i,], na.rm=T)
}

hist(maxpos)
hist(maxret)
hist(minpos)
hist(minret)

dev.off()
