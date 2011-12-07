library(zoo)
library(tseries)
library(RSQLite)
library(fractal)

source('util.r')

calhurst <- function(drv, left, right, betafrom, startdate, enddate, beta, scale.max, scale.min, scale.ratio)
{
    s.zoo = getquote(dbdrv, c(left, right), startdate-trunc(1.9*scale.max), enddate)
    snames = names(s.zoo)

    date1 = start(window(s.zoo, start=startdate, end=startdate+20))
    date2 = start(s.zoo)
    index1 = which(index(s.zoo)==date1)
    index2 = which(index(s.zoo)==date2)
    if ((index1-index2+1) < scale.max) stop('not long enough data')

    s.zoo = s.zoo[(index1-scale.max+1):NROW(s.zoo)]

    sprd <- apply(s.zoo, 1, function(x) {x[1] - sum(x[-1]*beta)})
    sprd <- zoo(as.vector(sprd), index(s.zoo))

    hexp <- rollapply(sprd, scale.max, function(z){DFA(z, scale.max=scale.max, scale.min=scale.min, scale.ratio=scale.ratio)[[1]]}, align='right')
}

args <- commandArgs(TRUE)
Sys.setlocale(category = "LC_TIME", locale = "C")

if (length(args) < 1) stop('hurst.r plan-file')

print(args)
plan <- read.table(args[1], row.names=1, sep='=', colClasses='character', strip.white=TRUE)

startdate = as.Date(plan['visualfrom', 1])
enddate = as.Date(plan['visualto', 1])

drv = dbDriver('SQLite')
con <- dbConnect(drv, dbname = plan['cointdb', 1])

tovisual <- dbGetQuery(con, plan['visuallist', 1])
betafrom <- plan['betafrom', 1]

pttest <- dbReadTable(con, betafrom)
tovisual <- merge(tovisual, pttest, by='cpair', all=FALSE)
rownames(tovisual) <- tovisual$cpair
dbDisconnect(con)

scale.max = as.integer(plan['scale.max', 1])
scale.min = as.integer(plan['scale.min', 1])
scale.ratio = as.integer(plan['scale.ratio', 1])
hurstdb = dbConnect(drv, dbname=plan['hurstdb' ,1])

olddir=setwd(plan['dbdir', 1])
for (i in 1:nrow(tovisual))
{
    cpair <- tovisual[i,]$cpair
    tmp <- unlist(strsplit(cpair, "\\."))
    left <- tmp[1]
    right <- tmp[2:length(tmp)]

    print(c(i, cpair))
    beta = as.numeric(unlist(strsplit(tovisual[i,]$beta, ';')))
    #beta = rep(1, length(right)) / length(right)

    hrst = calhurst(drv, left, right, betafrom, startdate, enddate, beta, scale.max, scale.min, scale.ratio)
    
    tbname = paste('hurst', cpair, scale.max, scale.min, scale.ratio, sep='.')
    creattbl = sprintf('create table if not exists [%s] ([date] text unique, [h] real)', tbname)
    dbGetQuery(hurstdb, creattbl)

    for (i in 1:NROW(hrst))
    {
        tmp = hrst[i]
        updttbl = sprintf('INSERT OR REPLACE INTO [%s] values ("%s", %f)', tbname, format(index(tmp)), as.numeric(tmp))
        dbGetQuery(hurstdb, updttbl)
    }
}
setwd(olddir)

# TODO: update hurst db

dbDisconnect(hurstdb)
dbUnloadDriver(drv)
warnings()
