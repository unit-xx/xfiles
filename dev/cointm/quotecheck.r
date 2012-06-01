# purpose: check stock price (hou fu quan) is near continuous.
# input: directory, security list
# result: a pdf with stock price, return rate, rr distribution and rr digests.

library(zoo)
library(tseries)
library(RSQLite)

source('util.r')

args <- commandArgs(TRUE)
if (length(args) < 2) stop('quotecheck.r directory sec-list-fn')
Sys.setlocale(category = "LC_TIME", locale = "C")

seclist <- read.table(args[2])
drv = dbDriver('SQLite')

setwd(args[1])
for (i in 1:NROW(seclist))
{
    qfn = seclist[i,]
    con <- dbConnect(drv, dbname = paste(qfn, 'db', sep='.'))
    s0 <- dbReadTable(con, 'data')
    dbDisconnect(con)
    Encoding(s0$name) = 'UTF-8'
    s0_date <- as.Date(as.character(s0$date), '%Y%m%d')
    quote <- s0[,'close']*s0[,'factor']
    s.zoo <- zoo(quote, s0_date)

    if(NROW(s.zoo)==0) next

    # calc digest
    rrate = quote[2:length(quote)] / quote[1:length(quote)-1] - 1
    rrate = zoo(rrate, index(s.zoo)[2:NROW(s.zoo)])
    print(qfn)
    print(rrate[which(rrate>0.08),])
    print(' ')

    pdf(paste(qfn,'pdf',sep='.'), width=17.55, height=8.3)
    # plot stock price
    plot(s.zoo, main=qfn)
    # plot return rate
    plot(rrate, main=qfn)
    # plot rr distribution
    #barplot(rrate, main=qfn)
    dev.off()
}
setwd('..')
