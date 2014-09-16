library(zoo)
library(TTR)

args = commandArgs(T)
# calculate Smart Money Index. SMI is defined as: 

# read 5min quote data

qfn.base = '000001'
if(length(args)>0)
{
  qfn.base = args[1]
}

qfn = paste(qfn.base, 'csv', sep='.')

quote = read.csv(qfn, stringsAsFactors=F)
datetime = data.frame(matrix(unlist(strsplit(quote$time, ' ', fixed=T)), ncol=2, byrow=T), stringsAsFactors=F)
quote$date = datetime[,1]
quote$hms = datetime[,2]

# check quotes counts for each day
#dailycount = aggregate(quote, by=list(quote$date), FUN=NROW)
#plot(dailycount$close)

smifixcalc <- function(quote, firstn, lastn)
{
  unsmart = quote[firstn] - quote[1]
  smart = quote[length(quote)] - quote[length(quote)-lastn]
  #print(unsmart)
  #print(smart)
  return(smart-unsmart)
}

smifixcalc2 <- function(quote, firstn, lastn)
{
  unsmart = quote[firstn] - quote[1]
  smart = quote[length(quote)] - quote[length(quote)-lastn]
  #print(unsmart)
  #print(smart)
  return(smart+unsmart)
}


# calculate SMI fix for each day
qavg = (quote$open + quote$high + quote$low + quote$close)/4
qclose = aggregate(quote$close, by=list(quote$date), FUN=function(quote){return(quote[length(quote)])})[,2]
smifix = aggregate(qavg, by=list(quote$date), FUN=smifixcalc, 6, 6)[,2]
smifix2 = aggregate(qavg, by=list(quote$date), FUN=smifixcalc2, 6, 6)[,2]

# add SMI fix to original quote.
qzoo = zoo(cbind(close=qclose, smifix=smifix, cumfix=cumsum(smifix), smifix2=smifix2, cumfix2=cumsum(smifix2)), as.Date(unique(quote$date)))
qzoo$smiroll14 = rollapplyr(qzoo$smifix, 14, sum)
qzoo$smiroll21 = rollapplyr(qzoo$smifix, 21, sum)
qzoo$smi2roll14 = rollapplyr(qzoo$smifix2, 14, sum)
qzoo$smi2roll21 = rollapplyr(qzoo$smifix2, 21, sum)

macd1 = MACD(qzoo$cumfix2, 5,10,5)
qzoo = cbind(qzoo, macd1)

pdf(paste(qfn.base, 'pdf', sep='.'), width=17.55, height=11.07)
plot(qzoo[,c('close', 'smiroll21', 'smiroll14')], main=qfn.base)
plot(qzoo[,c('close', 'smi2roll21', 'smi2roll14')], main=qfn.base)
dev.off()
