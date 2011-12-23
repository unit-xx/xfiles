library(zoo)
library(RSQLite)
library(PerformanceAnalytics)

source('util.r')

# given a pair and its beta, trade benchmarking using upper/lower bound params.
# results: opent/closet/earn/cost

pairbm <- function (dbdrv, left, right, startdate, enddate, beta, upper, lower, hlife, decay)
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

    ret = spreadbm2(sprd, s.zoo, c(1, -beta), upper, lower, dir='short')
    ret
}

args <- commandArgs(TRUE)
if (length(args) < 1) stop("tradebm.r visualplan")

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
decay = as.numeric(plan['decay', 1])
betafrom <- plan['betafrom', 1]
pttest <- dbReadTable(con, betafrom)

tovisual <- merge(tovisual, pttest, by='cpair', all=FALSE)
rownames(tovisual) <- tovisual$cpair

summary <- data.frame(stringsAsFactors=FALSE)

setwd(plan['dbdir', 1])
for (i in 1:nrow(tovisual))
{
    cpair <- tovisual[i,]$cpair
    beta = as.numeric(unlist(strsplit(tovisual[i,]$beta, ';')))

    tmp <- unlist(strsplit(cpair, "\\."))
    left <- tmp[1]
    right <- tmp[2:length(tmp)]
    print(c(i, cpair))

    upper = upper.default
    lower = lower.default
    q = sprintf('select upper, lower from tradeparam where cpair="%s"', cpair)
    ul = dbGetQuery(con, q)
    if (nrow(ul) > 0)
    {
        upper = ul$upper
        lower = ul$lower
    }

    hlife <- as.numeric(tovisual[i,]$hlife)

    ret = pairbm(drv, left, right, startdate, enddate, beta, upper, lower, hlife, decay)
    ret = cbind(ret, upper=upper, lower=lower, hlife=hlife, decay=decay, beta=tovisual[i,]$beta, betafrom=betafrom)
    write.table(ret, paste(left,paste(right,collapse='.'),tag,'trdbm',sep='.'), row.names=FALSE)

    summary = rbind(summary, cbind(cpair=cpair, bmstat(ret), upper=upper, lower=lower, hlife=hlife, decay=decay, beta=tovisual[i,]$beta, betafrom=betafrom))
}
write.table(summary, paste(tag, format(startdate, format='%Y%m%d'), format(enddate, format='%Y%m%d'), 'trdstat',sep='.'), row.names=FALSE)

dbDisconnect(con)
dbUnloadDriver(drv)
warnings()

