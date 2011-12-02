# tradebm.r only gives trade result, this script shows how earning grows dynamically

library(zoo)
library(RSQLite)

source('util.r')

# given a pair and its beta, trade benchmarking using upper/lower bound params,
# and draw the returns figure

pairbm.draw <- function (dbdrv, left, right, startdate, enddate, betafrom, beta, upper, lower, hlife, decay)
{
    s.zoo = getquote(dbdrv, c(left, right), startdate, enddate)
    snames = names(s.zoo)

    sprd <- apply(s.zoo, 1, function(x) {x[1] - sum(x[-1]*beta)})
    sprd <- zoo(as.vector(sprd), index(s.zoo))

    bmrst = read.table(paste(left,paste(right,collapse='.'),tag,'trdbm',sep='.'), header=T, stringsAsFactors=F)

    if (decay < 0) decay = round(hlife * -decay)

    relret = zoo(0, index(s.zoo))
    absret = zoo(0, index(s.zoo))

    # caculate return for each day, merge them all and get cumsum
    for (i in 1:nrow(bmrst))
    {
        trd = bmrst[i,]
        ret = trd$opendir * diff(window(sprd, start=as.Date(trd$opent), end=as.Date(trd$closet)))
        absret = merge(absret, ret, all=T, fill=0)
        relret = merge(relret, ret/trd$holdcap, all=T, fill=0)
    }
    relret[,1] <- apply(relret, 1, function(x) {sum(x)})
    relret = 1 + cumsum(relret[,1])
    absret[,1] <- apply(absret, 1, function(x) {sum(x)})
    absret = cumsum(absret[,1])

    abscost = sum(bmrst$tcost)
    relcost = sum(bmrst$tcost/bmrst$holdcap)
    absallret = as.numeric(tail(absret,1)) - abscost
    relallret = as.numeric(tail(relret,1)) - relcost

    pdf(paste(left,paste(right,collapse='.'),tag,'trdbm','pdf',sep='.'), width=17.55, height=8.3)
    ylim = c(min(relret), max(relret))
    plot(relret, ylim=ylim)
    abline(v=as.Date(unique(as.yearmon(index(relret)))),
           h=seq(round(ylim[1],2),ylim[2],0.01),
           col='grey',lty='dashed',lwd=1)
    abline(h=relallret, col='red', lty='dashed')
    for (i in 1:nrow(bmrst))
    {
        trd = bmrst[i,]
        x = as.Date(c(trd$opent, trd$closet))
        xy = relret[x,]
        color = ifelse((bmrst[i,]$opendir == 1), 'red', 'green')
        lines(xy, col=color, lwd=2)
        
        x = as.Date(trd$closet)
        r = as.numeric(relret[x])
        y = c(r, r-trd$tcost/trd$holdcap)
        lines(c(x,x), y, col='red', lwd=3)
    }

    title('Relative Returns (with Tx cost)')
    titlestr = sprintf('%s(in=%s) %s.%s\nupper=%.2f lower=%.2f\nabs.Txcost=%.2f rel.Txcost=%.2f\nabs.ret=%.2f rel.ret=%.4f',
                        tag, betafrom,
                        left, paste(right,collapse='.'),
                        upper, lower, abscost, relcost,
                        absallret, relallret)
    mtext(titlestr, family='song', padj=1)

    ylim = c(min(absret), max(absret))
    plot(absret, ylim=ylim)
    abline(v=as.Date(unique(as.yearmon(index(absret)))),
           h=seq(round(ylim[1],-1),ylim[2],10),
           col='grey',lty='dashed',lwd=1)
    abline(h=absallret, col='red', lty='dashed')
    for (i in 1:nrow(bmrst))
    {
        trd = bmrst[i,]
        x = as.Date(c(trd$opent, trd$closet))
        xy = absret[x,]
        color = ifelse((bmrst[i,]$opendir == 1), 'red', 'green')
        lines(xy, col=color, lwd=2)
        
        x = as.Date(trd$closet)
        r = as.numeric(absret[x])
        y = c(r, r-trd$tcost)
        lines(c(x,x), y, col='red', lwd=3)
    }
    title('Absolute Returns (with Tx cost)')
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
upper.default <- as.numeric(plan['upper.default', 1])
lower.default <- as.numeric(plan['lower.default', 1])
betafrom <- plan['betafrom', 1]
decay = as.numeric(plan['decay', 1])
pttest <- dbReadTable(con, betafrom)

tovisual <- merge(tovisual, pttest, by='cpair', all=FALSE)

setwd(plan['dbdir', 1])
for (i in 1:nrow(tovisual))
{
    cpair <- tovisual[i,]$cpair
    beta = as.numeric(unlist(strsplit(tovisual[i,]$beta, ';')))

    upper = upper.default
    lower = lower.default
    q = sprintf('select upper, lower from tradeparam where cpair="%s"', cpair)
    ul = dbGetQuery(con, q)
    if (nrow(ul) > 0)
    {
        upper = ul$upper
        lower = ul$lower
    }

    tmp <- unlist(strsplit(cpair, "\\."))
    left <- tmp[1]
    right <- tmp[2:length(tmp)]
    print(c(left, right))

    hlife <- as.numeric(tovisual[i,]$hlife)
    pairbm.draw(drv, left, right, startdate, enddate, betafrom, beta, upper, lower, hlife, decay)
}
dbDisconnect(con)
dbUnloadDriver(drv)
warnings()

