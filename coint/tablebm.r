# enumerate open/close threshold and computing earnings.

library(zoo)
library(RSQLite)

source('util.r')

tablebm <- function (dbdrv, left, right, startdate, enddate, beta, uprange, lorange, decay=0)
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

    ul = merge(uprange, lorange)

    ret = data.frame()
    for (i in 1:nrow(ul))
    {
        u = ul[i,][[1]]
        l = ul[i,][[2]]
        bmrst = spreadbm(sprd, s.zoo, u, l, decay)
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

    ret = tablebm(drv, left, right, startdate, enddate, beta, uprange, lorange, 22*6)
    #print(ret)
    write.table(ret, paste(left,right,tag,'tblbm',sep='.'), row.names=FALSE)
}
setwd('..')

# wireframe(tearn~u*l, data=d, shade=TRUE, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),)
