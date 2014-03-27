library(zoo)
library(chron)
library(moments)

# explore trading volume, price diff statistics of IF quotations.

Sys.setlocale(category = "LC_TIME", locale = "C")

qfns = c('201209.if2','201210.if2','201211.if2','201212.if2','201301.if2')
#qfns = c('201212.if2')
#qfns = c('20121116.if2')
aggunit = 'days'

for (fn in qfns)
{
  print(sprintf('Processing ... %s', fn))
  q2 = read.table(fn, header=T, quote="\"", stringsAsFactors=F, 
                  colClasses=c('character','character','integer',
                         'character','numeric','numeric','numeric','numeric'))
  
  # dates and times series as zoo index
  dts = dates(q2$tradeday, format="ymd")
  tms = times(q2$tradetime, format='h:m:s')
  
  # trading hour
  tradeintval = which(tms > times('09:15:00') & tms < times('15:15:00'))
  
  tindex = as.POSIXct(paste(q2$tradeday, q2$tradetime), format="%Y%m%d %H:%M:%OS")
  
  q2.zoo = zoo(q2[,c(3,5,6,7,8)], tindex)
  q2.zoo = q2.zoo[tradeintval,]
  
  aggidx = as.POSIXct(trunc(index(q2.zoo), aggunit))
  
  #qbv = aggregate(q2.zoo$buyvolume1, by=aggidx, FUN=quantile)
  #qsv = aggregate(q2.zoo$sellvolume1, by=aggidx, FUN=quantile)
  
  dayidx = as.POSIXct(trunc(index(q2.zoo), 'days'))
  
  bpdiff = do.call(rbind, lapply(split(q2.zoo$buyprice1, dayidx), diff))
  spdiff = do.call(rbind, lapply(split(q2.zoo$sellprice1, dayidx), diff))
  
  #aggidx2 = as.POSIXct(trunc(index(bpdiff), aggunit))
  
  #qbpdiff = aggregate(bpdiff, by=aggidx2, FUN=quantile)
  #qspdiff = aggregate(spdiff, by=aggidx2, FUN=quantile)
  
  pdf(paste(fn, aggunit, 'pdf', sep='.'), width=17.55, height=8.3)
  
  hb = hist(q2.zoo$buyvolume1, breaks=unique(q2.zoo$buyvolume1), main=sprintf('buy volume histgram'))
  plot(log(hb$mids), log(hb$density),main=sprintf('buy volume histgram (log-log scale)'))
  
  hs = hist(q2.zoo$sellvolume1, breaks=unique(q2.zoo$sellvolume1), main=sprintf('sell volume histgram'))
  plot(log(hs$mids), log(hs$density),main=sprintf('sell volume histgram (log-log scale)'))
  
  hist(bpdiff, breaks=unique(bpdiff), 
       main=sprintf('buy price diff histgram, kurtosis=%.2f', kurtosis(bpdiff)))
  
  #qqnorm(bpdiff, main='Normal qqplot of buy price diff')
  
  hist(spdiff, breaks=unique(spdiff), 
       main=sprintf('sell price diff histgram, kurtosis=%.2f', kurtosis(spdiff)))
  
  #qqnorm(spdiff, main='Normal qqplot of sell price diff')

  #plot(qbv, type='o', pch='+', main='buy volumne quantile')
  #plot(qsv, type='o', pch='+', main='sell volumne quantile')
  #plot(qbpdiff, type='o', pch='+', main='buy price diff quantile')
  #plot(qspdiff, type='o', pch='+', main='sell price diff quantile')
  dev.off()
}
