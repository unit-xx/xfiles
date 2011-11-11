library(zoo)
library(RSQLite)

source('util.r')

# given a pair and its beta, trade benchmarking using upper/lower bound params.
# results: opent/closet/earn/cost

pairbm <- function (dbdrv, left, right, startdate, enddate, beta, upper, lower, decay=0)
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

    ret = spreadbm(sprd, s.zoo, upper, lower, decay)
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
    beta <- as.numeric(tovisual[i,]$beta)

    tmp <- unlist(strsplit(cpair, "\\."))
    left <- tmp[1]
    right <- tmp[2]
    print(c(left, right))

    ret = pairbm(drv, left, right, startdate, enddate, beta, upper, lower, 22*6)
    write.table(ret, paste(left,right,tag,'trdbm',sep='.'), row.names=FALSE)
}
dbUnloadDriver(drv)
warnings()

