# tradebm.r only gives trade result, this script shows how earning grows dynamically

library(zoo)
library(RSQLite)

source('util.r')

# given a pair and its beta, trade benchmarking using upper/lower bound params,
# and draw the returns figure

pairbm.draw <- function (dbdrv, left, right, npair, startdate, enddate, betafrom, beta, upper, lower, decay=0)
{
    con <- dbConnect(drv, dbname = paste(left, 'db', sep='.'))
    s1 <- dbReadTable(con, 'data')
    dbDisconnect(con)
    Encoding(s1$name) = 'UTF-8'
    s1_date <- as.Date(as.character(s1$date), '%Y%m%d')

    con <- dbConnect(drv, dbname = paste(right, 'db', sep='.'))
    s2 <- dbReadTable(con, 'data')
    dbDisconnect(con)
    Encoding(s2$name) = 'UTF-8'
    s2_date <- as.Date(as.character(s2$date), '%Y%m%d')

    s1 <- zoo(s1$close, s1_date)
    s2 <- zoo(s2$close, s2_date)

    s.zoo <- merge(s1, s2, all=FALSE)
    s.zoo <- window(s.zoo, start=startdate, end=enddate)

    sprd <- s.zoo$s1 - beta*(s.zoo$s2)

    bmrst = spreadbm(sprd, s.zoo, upper, lower, decay)

    returns = zoo(0, index(s.zoo))

    # caculate return for each day, merge then all and get cumsum
    for (i in 1:nrow(bmrst))
    {
        trd = bmrst[i,]
        ret = trd$opendir * diff(window(sprd, start=trd$opent, end=trd$closet))
        returns = merge(returns, ret, all=TRUE, incomparables=0)
    }
    returns[,1] <- apply(returns, 1, function(x) {sum(x, na.rm=TRUE)})
    returns = cumsum(returns[,1])

    pdf(paste(left,right,tag,'trdbm','pdf',sep='.'), width=17.55, height=8.3)
    plot(returns)
    ylim = c(min(returns, na.rm=TRUE), max(returns, na.rm=TRUE))
    abline(v=as.Date(unique(as.yearmon(index(returns)))),
           h=seq(round(ylim[1],-2),round(ylim[2],-1),50),
           col='lightgrey',lty='dotted',lwd=1)

    title('Abosolute Returns (with Tx cost)')
    titlestr = sprintf('%s(in=%s) %s.%s.%s\nupper=%.2f lower=%.2f\nTxcost=%.2f',
                        tag, betafrom,
                        left, right, npair,
                        upper, lower, sum(bmrst$tcost))
    mtext(titlestr, family='song', padj=1)
    dev.off()
}

Sys.setlocale(category = "LC_TIME", locale = "C")

args <- commandArgs(TRUE)
if (length(args) < 1) stop("tradebm.draw.r visualplan")

print(args)
plan <- read.table(args[1], row.names=1, sep='=', colClasses='character', strip.white=TRUE)

startdate = as.Date(plan['visualfrom', 1])
enddate = as.Date(plan['visualto', 1])
tag = plan['tag', 1]

drv = dbDriver('SQLite')
con <- dbConnect(drv, dbname = plan['cointdb', 1])
tovisual <- dbGetQuery(con, plan['visuallist', 1])
upper <- as.numeric(plan['upper', 1])
lower <- as.numeric(plan['lower', 1])
betafrom <- plan['betafrom', 1]
pttest <- dbReadTable(con, betafrom)
dbDisconnect(con)

tovisual <- merge(tovisual, pttest, by='cpair', all=FALSE)

setwd(plan['dbdir', 1])
for (i in 1:nrow(tovisual))
{
    cpair <- tovisual[i,]$cpair
    npair <- tovisual[i,]$npair
    npair <- iconv(npair, from='UTF-8', to='GBK')
    beta <- as.numeric(tovisual[i,]$beta)

    tmp <- unlist(strsplit(cpair, "\\."))
    left <- tmp[1]
    right <- tmp[2]
    print(c(left, right))

    pairbm.draw(drv, left, right, npair, startdate, enddate, betafrom, beta, upper, lower, 22*6)
}
dbUnloadDriver(drv)
warnings()

