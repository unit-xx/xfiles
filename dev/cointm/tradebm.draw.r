# tradebm.r only gives trade result, this script shows how earning grows dynamically

library(zoo)
library(RSQLite)

source('util.r')

# given a pair and its beta, trade benchmarking using upper/lower bound params,
# and draw the returns figure

pairbm.draw <- function (dbdrv, left, right, startdate, enddate, betafrom, beta, upper, lower, hlife, decay)
{
    s.zoo = getquote(dbdrv, c(left, right), seq(startdate, length=2, by='-1 years')[2] , enddate)
    snames = names(s.zoo)

    sprd <- apply(s.zoo, 1, function(x) {x[1] - sum(x[-1]*beta)})
    sprd <- zoo(as.vector(sprd), index(s.zoo))

    bmrst = read.table(paste(left,paste(right,collapse='.')), header=T, stringsAsFactors=F)

    relret = zoo(0, index(s.zoo))
    absret = zoo(0, index(s.zoo))

    # caculate return for each day, merge then all and get cumsum
    for (i in 1:nrow(bmrst))
    {
        trd = bmrst[i,]
        ret = trd$opendir * diff(window(sprd, start=as.Date(trd$opent), end=as.Date(trd$closet)))
        absret = merge(absret, ret, all=T, fill=0)
        relret = merge(absret/trd$holdcap, ret, all=T, fill=0)
    }
    relret[,1] <- apply(relret, 1, function(x) {sum(x)})
    relret = 1 + cumsum(relret[,1])
    absret[,1] <- apply(absret, 1, function(x) {sum(x)})
    absret = cumsum(absret[,1])

    pdf(paste(left,paste(right,collapse='.'),tag,'trdbm','pdf',sep='.'), width=17.55, height=8.3)
    plot(relret)
    ylim = c(min(relret), max(relret))
    abline(v=as.Date(unique(as.yearmon(index(returns)))),
           h=seq(round(ylim[1],2),ylim[2],0.01),
           col='grey',lty='dashed',lwd=1)
    title('Abosolute Returns (with Tx cost)')

    plot(relret)
    ylim = c(min(relret), max(relret))
    abline(v=as.Date(unique(as.yearmon(index(returns)))),
           h=seq(round(ylim[1],2),ylim[2],0.01),
           col='grey',lty='dashed',lwd=1)

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

