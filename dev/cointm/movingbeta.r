library(RSQLite)
library(zoo)

source('util.r')

Sys.setlocale(category = "LC_TIME", locale = "C")

drv = dbDriver('SQLite')
codes = c('000300', '000908', '000911', '000917')
setwd('hs300indexout')

s.zoo = getquote(drv, codes, as.Date('2005-01-01'), as.Date('2011-12-31'))

b = getbeta(s.zoo, seq(as.Date('2011-02-01'), as.Date('2012-01-01'), 'month')-1)

b = rbind(zoo(as.matrix(b[1,]), start(s.zoo)), b)

print(b)

s.zoo = merge(s.zoo, b)
s.zoo = na.locf(s.zoo)
print(head(s.zoo))

sprd = apply(s.zoo, 1, function(x) {x[1] - sum(x[2:4]*x[6:8])})

pdf(width=17.55, height=8.3)
sprd = zoo(sprd, index(s.zoo))
sprd = window(sprd, start=as.Date('2011-01-01'), end=as.Date('2011-12-31'))
#ylim = c(min(sprd), max(sprd))
ylim = c(-350, 0)
plot(sprd, ylim=ylim)
abline(v=as.Date(unique(as.yearmon(index(sprd)))),
       h=seq(round(ylim[1],-2),round(ylim[2],-1),50),
       col='lightgrey',lty='dotted',lwd=1)

dev.off()

dbUnloadDriver(drv)

