# plot stat generated by scpstat.py

library(ggplot2)

args = commandArgs(T)

statfn = '20140812/scpstrat1.2014-08-12.stat'
pdfn = '20140812/scpstrat1.2014-08-12.stat2.pdf'

if(length(args) >= 2)
{
  statfn = args[1]
  pdfn = args[2]
}

trend <- function(p, tnum)
{
  y = p
  x = 1:tnum
  lmr = lm(y~x)
  return(coef(lmr)[2])
}

propstat <- function(prop, y, xunit, tx, propname)
{
  xbin = round(prop/xunit)*xunit
  
  ytx.agg = aggregate(y-tx, by=list(prop=factor(xbin)), FUN=sum)
  y.agg = aggregate(y, by=list(prop=factor(xbin)), FUN=sum)
  
  dfn2 = data.frame(xbin, y)
  
  # y distribution according to prop range
  g = ggplot(dfn2, aes(x=factor(xbin), fill=factor(y))) + geom_bar(stat='bin') + xlab(propname) + ggtitle('Distribution')
  plot(g)
  
  # y sum, with/without tx
  g = ggplot(y.agg, aes(x=factor(prop), y=x)) + geom_bar(stat='identity') + xlab(propname) + ggtitle('Aggregated earning, Before Tx')
  plot(g)
  g = ggplot(ytx.agg, aes(x=factor(prop), y=x)) + geom_bar(stat='identity') + xlab(propname) + ggtitle('Aggregated earning, After Tx')
  plot(g)
  
  # a simple way is like below, but is has confusing x-axis.
  #ggplot(a, aes(x=prop,fill=factor(y)))+geom_bar(binwidth=0.05)
  #ggplot(a, aes(x=factor(prop),fill=factor(y)))+geom_bar(binwidth=0.05)
}

stat = read.csv(statfn, header=T)
stat.m = as.matrix(stat)

# prepare datas: prices and volumes
if (stat$tdir[1]==-1)
{
  # ask price trend
  prices3 = stat[,paste('ask', 1+3:1, sep='')]
  prices5 = stat[,paste('ask', 1+5:1, sep='')]
  prices7 = stat[,paste('ask', 1+7:1, sep='')]
  
  same3 = stat[,paste('askvol', 3:1, sep='')]
  same5 = stat[,paste('askvol', 5:1, sep='')]
  same7 = stat[,paste('askvol', 7:1, sep='')]

  oppo3 = stat[,paste('bidvol', 3:1, sep='')]
  oppo5 = stat[,paste('bidvol', 5:1, sep='')]
  oppo7 = stat[,paste('bidvol', 7:1, sep='')]
} else
{
  prices3 = stat[,paste('bid', 1+3:1, sep='')]
  prices5 = stat[,paste('bid', 1+5:1, sep='')]
  prices7 = stat[,paste('bid', 1+7:1, sep='')]

  same3 = stat[,paste('bidvol', 3:1, sep='')]
  same5 = stat[,paste('bidvol', 5:1, sep='')]
  same7 = stat[,paste('bidvol', 7:1, sep='')]
  
  oppo3 = stat[,paste('askvol', 3:1, sep='')]
  oppo5 = stat[,paste('askvol', 5:1, sep='')]
  oppo7 = stat[,paste('askvol', 7:1, sep='')]
}

# tick trends vs earning

trend3 = apply(prices3, 1, FUN=trend, 3)
trend5 = apply(prices5, 1, FUN=trend, 5)
trend7 = apply(prices7, 1, FUN=trend, 7)

# same side orderbook volume, absolute number and ratio to opposite volume

lastnum = same3[,3]
opponum = oppo3[,3]
lastratio = same3[,3]/oppo3[,3]

last3num.max = apply(same3, 1, FUN=max)
last3num.avg = apply(same3, 1, FUN=mean)
last3ratio.max = apply(same3/oppo3, 1, FUN=max)
last3ratio.avg = apply(same3/oppo3, 1, FUN=mean)

last5num.max = apply(same5, 1, FUN=max)
last5num.avg = apply(same5, 1, FUN=mean)
last5ratio.max = apply(same5/oppo5, 1, FUN=max)
last5ratio.avg = apply(same5/oppo5, 1, FUN=mean)

last7num.max = apply(same7, 1, FUN=max)
last7num.avg = apply(same7, 1, FUN=mean)
last7ratio.max = apply(same7/oppo7, 1, FUN=max)
last7ratio.avg = apply(same7/oppo7, 1, FUN=mean)

# opposite orderbook volume, absolute number and ratio to same side volume

statpdf = pdf(pdfn, width=17.55, height=11.07)

earn = round(stat$earn, 1)

propstat(trend3, earn, 0.05, 0.14, quote(trend3))
propstat(trend5, earn, 0.05, 0.14, quote(trend5))
propstat(trend7, earn, 0.05, 0.14, quote(trend7))

propstat(log(lastnum), earn, 0.2, 0.14, quote(lastnum))
propstat(log(opponum), earn, 0.2, 0.14, quote(opponum))
propstat(log(lastratio), earn, 0.2, 0.14, quote(lastratio))

propstat(log(last3num.max), earn, 0.2, 0.14, quote(last3num.max))
propstat(log(last3num.avg), earn, 0.2, 0.14, quote(last3num.avg))
propstat(log(last3ratio.max), earn, 0.2, 0.14, quote(last3ratio.max))
propstat(log(last3ratio.avg), earn, 0.2, 0.14, quote(last3ratio.avg))

propstat(log(last5num.max), earn, 0.2, 0.14, quote(last5num.max))
propstat(log(last5num.avg), earn, 0.2, 0.14, quote(last5num.avg))
propstat(log(last5ratio.max), earn, 0.2, 0.14, quote(last5ratio.max))
propstat(log(last5ratio.avg), earn, 0.2, 0.14, quote(last5ratio.avg))

propstat(log(last7num.max), earn, 0.2, 0.14, quote(last7num.max))
propstat(log(last7num.avg), earn, 0.2, 0.14, quote(last7num.avg))
propstat(log(last7ratio.max), earn, 0.2, 0.14, quote(last7ratio.max))
propstat(log(last7ratio.avg), earn, 0.2, 0.14, quote(last7ratio.avg))

dev.off()

# $Id$
