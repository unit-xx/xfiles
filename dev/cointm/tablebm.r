# enumerate open/close threshold and computing earnings.

library(zoo)
library(RSQLite)
library(PerformanceAnalytics)

source('util.r')

tablebm <- function (dbdrv, left, right, startdate, enddate, beta, uprange, lorange, hlife, decay)
{
    s.zoo = getquote(dbdrv, c(left, right), seq(startdate, length=2, by='-1 years')[2] , enddate)
    snames = names(s.zoo)

    sprd <- apply(s.zoo, 1, function(x) {x[1] - sum(x[-1]*beta)})
    sprd <- zoo(as.vector(sprd), index(s.zoo))

    if (decay < 0) decay = round(hlife * -decay)

    emeanline <- ema(sprd, lambda=2.8854*decay)
    emean2line <- ema(sprd**2, lambda=2.8854*decay)
    esdline <- sqrt(emean2line - emeanline**2)
    sprd = cbind(sprd=sprd, mean=emeanline, sd=esdline)

    sprd = window(sprd, start=startdate, end=enddate)
    s.zoo = window(s.zoo, start=startdate, end=enddate)

    ul = merge(uprange, lorange)

    ret = data.frame()
    for (i in 1:nrow(ul))
    {
        u = ul[i,][[1]]
        l = ul[i,][[2]]
        bmrst = spreadbm2(sprd, s.zoo, c(1, -beta), u, l, dir='short')
        pstat = bmstat(bmrst)
        pstat = cbind(u=u, l=l, pstat)
        ret = rbind(ret, pstat)
    }
    ret
}

args <- commandArgs(TRUE)
if (length(args) < 1) stop("tablebm.r visualplan")

print(args)
plan <- read.table(args[1], row.names=1, sep='=', colClasses='character', strip.white=TRUE)

startdate = as.Date(plan['visualfrom', 1])
enddate = as.Date(plan['visualto', 1])
tag = plan['tag', 1]

drv = dbDriver('SQLite')
con <- dbConnect(drv, dbname = plan['cointdb', 1])
tovisual <- dbGetQuery(con, plan['visuallist', 1])

r = as.numeric(unlist(strsplit(plan['uprange', 1], ":")))
uprange = seq(r[1], r[2], r[3])
r = as.numeric(unlist(strsplit(plan['lorange', 1], ":")))
lorange = seq(r[1], r[2], r[3])

decay = as.numeric(plan['decay', 1])
betafrom <- plan['betafrom', 1]
pttest <- dbReadTable(con, betafrom)
dbDisconnect(con)

tovisual <- merge(tovisual, pttest, by='cpair', all=FALSE)
rownames(tovisual) <- tovisual$cpair

setwd(plan['dbdir', 1])
for (i in 1:nrow(tovisual))
{
    cpair <- tovisual[i,]$cpair
    beta = as.numeric(unlist(strsplit(tovisual[i,]$beta, ';')))

    tmp <- unlist(strsplit(cpair, "\\."))
    left <- tmp[1]
    right <- tmp[2:length(tmp)]

    hlife <- as.numeric(tovisual[i,]$hlife)

    ts = Sys.time()
    ret = tablebm(drv, left, right, startdate, enddate, beta, uprange, lorange, hlife, decay)
    te = Sys.time()
    print(sprintf("tablebm (%d) %s in %s", i, cpair, format(te-ts)))
    write.table(ret, paste(cpair,tag,'tblbm',sep='.'), row.names=FALSE)
}
setwd('..')
