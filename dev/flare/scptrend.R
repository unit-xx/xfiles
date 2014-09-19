# see also scptrend.py. We follow the trend to buy/sell the contract, and how is the return goes.

args = commandArgs(T)

trendfn = 'xxx'
pdfn = 'xxx.pdf'

if(length(args) >= 2)
{
  trendfn = args[1]
  pdfn = args[2]
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

ret.aggall = apply(ret, MARGIN=2, FUN=mean)
ret.aggpart = apply(ret[which(seequote==1),], MARGIN=2, FUN=mean)

pdf(pdfn, width=17.55, height=11.07)

for(i in 1:length(odir))
{
    plot(1:NCOL(ret), ret[i,], type='b', pch='+', xlab='tick', ylab='earn', main=sprintf('odir=%d earn=%.2f seequote=%d', odir[i], earn[i], seequote[i]))    
    abline(h=-1, col='red')
}

dev.off()

simretsum = rep(0.0, 5)
maxpos = rep(0.0, length(odir))
for(i in 1:length(odir))
{
  if(seequote[i]!=8)
  {
    if(min(ret[i,],na.rm=T)<=-1)
    {
      simretsum = simretsum + (-1.0)
    }
    else{
      simretsum[1] = simretsum[1] + max(ret[i,],na.rm=T)
      simretsum[2] = simretsum[2] + ifelse(is.na(ret[i,40]), 0, ret[i,40])
      simretsum[3] = simretsum[3] + ifelse(is.na(ret[i,60]), 0, ret[i,60])
      simretsum[4] = simretsum[4] + ifelse(is.na(ret[i,80]), 0, ret[i,80])
      simretsum[5] = simretsum[5] + ifelse(is.na(ret[i,90]), 0, ret[i,90])
      
      maxpos[i] = which.max(ret[i,])
    }
  }
}

print(simretsum)
