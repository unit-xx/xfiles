library(ggplot2)

punit = 10
billion = 1000000000

args = commandArgs(T)
if(length(args)>0)
{
  code = args[1]
}else
{
  code = '000001'
}

qfn = paste(code, 'csv', sep='.')
pdfn = paste(code, 'pdf', sep='.')

ph = read.csv(qfn, stringsAsFactors=F)

# filter out NA values
closenotna = which(!is.na(ph$close))
amtnotna = which(!is.na(ph$amt))
notna = intersect(closenotna, amtnotna)

ph = ph[notna,]
ph$amt = ph$amt/billion

# extract date part.
dates = matrix(unlist(strsplit(ph$time, split=' ')), ncol=2, byrow=T)
dates = as.Date(dates[,1])
year = format(dates, '%Y')

# round price is the price range for aggregation
roundprice = round(ph$close/punit) * punit

# apply decay for volumes: more recent trading volume weights more
# assume: exp(-365 * dacaycoef) = lambda
lambda = 0.618
decaycoef = -log(lambda) / 365
daydiff = as.integer(dates-dates[length(dates)])
decayratio = exp(daydiff * decaycoef)

# daily close price
price.dclose = aggregate(ph$close, by=list(yd=dates), FUN=tail, n=1)
price.dclose = as.matrix(price.dclose[,2])
rownames(price.dclose) = unique(format(dates))

# aggregate by year and price range
pricehist = aggregate(ph$amt, by=list(rp=roundprice, year=year), FUN=sum)

pricehist.decay = aggregate(ph$amt*decayratio, by=list(rp=roundprice, year=year), FUN=sum)

# aggregate in full range
pricehist.full = aggregate(ph$amt, by=list(rp=roundprice), FUN=sum)

# not necessary to use dcast if ggplot is used to draw bar plot.
#pricehist.cast = dcast(pricehist, year~rp, value.var='x', fill=0)
#rownames(pricehist.cast) = pricehist.cast[,1]
#pricehist.cast= pricehist.cast[,-1]

unqyear = unique(pricehist$year)
prange = round(range(pricehist.full$rp), -2)
vrange = range(pricehist.full$x)

pdf(pdfn, width=17.55, height=11.07)

# 1. plot histgram for each year on separate plot.
for(y in unqyear)
{
  # yearly price histgram
  yph = pricehist[which(pricehist$year==y),]
  #plot(yph$rp, yph$x, type='n', xlim=prange, ylim=vrange,
  #     xlab='price', ylab='volume/billion', main=y)
  #abline(v=seq(prange[1], prange[2], 100), col='lightgrey', lty='dotted')
  #lines(yph$rp, yph$x, type='h')
  x = ggplot(yph, aes(x=rp, y=x)) + geom_bar(stat='identity', color='lightgrey') + xlim(prange) + ylim(0, vrange[2]) + ggtitle(y)
  plot(x)
}

# 2. plot histgram for the full range

#plot(pricehist.full$rp, pricehist.full$x, xlab='price', ylab='volume/billion',
#     main=sprintf('%s to %s', dates[1], dates[length(dates)]), type='n',
#     xlim=prange, ylim=vrange)
#abline(v=seq(prange[1], prange[2], 100), col='lightgrey', lty='dotted')
#lines(pricehist.full$rp, pricehist.full$x, type='h')

#barplot(as.matrix(pricehist.cast[1:5,]), col = rainbow(6), beside=F, legend=rownames(pricehist.cast))
#        xlim=prange, ylim=vrange)


#chartSeries(price.dclose)
gf=ggplot(pricehist, aes(x=rp, y=x, fill=year)) + geom_bar(stat='identity', color='lightgrey') + ggtitle(sprintf('%s to %s', dates[1], dates[length(dates)])) + scale_x_continuous(breaks=seq(prange[1], prange[2], 100))

gd=ggplot(pricehist.decay, aes(x=rp, y=x, fill=year)) + geom_bar(stat='identity', color='lightgrey') + ggtitle(sprintf('lambda=%.3f %s to %s', lambda, dates[1], dates[length(dates)])) + scale_x_continuous(breaks=seq(prange[1], prange[2], 100))

plot(gf)
plot(gf+coord_flip())
plot(gd)
plot(gd+coord_flip())

dev.off()
