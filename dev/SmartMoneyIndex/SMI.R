library(zoo)

args = commandArgs(T)
# calculate Smart Money Index. SMI is defined as: 

# read 5min quote data

qfn.base = '000300'
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

smifixcalc <- function(quote)
{
  unsmart = quote[6] - quote[1]
  smart = quote[length(quote)] - quote[length(quote)-12]
  #print(unsmart)
  #print(smart)
  return(smart-unsmart)
}
# calculate SMI fix for each day
qavg = (quote$open + quote$high + quote$low + quote$close)/4
qclose = aggregate(quote$close, by=list(quote$date), FUN=function(quote){return(quote[length(quote)])})[,2]
smifix = aggregate(qavg, by=list(quote$date), FUN=smifixcalc)[,2]

# add SMI fix to original quote.
qzoo = zoo(cbind(close=qclose, smifix=smifix, cumfix=cumsum(smifix)), as.Date(unique(quote$date)))
qzoo$closefix = qzoo$close + qzoo$cumfix

pdf(paste(qfn.base, 'pdf', sep='.'), width=17.55, height=11.07)
plot(qzoo[,cbind('close', 'cumfix')], main=qfn.base)
dev.off()
