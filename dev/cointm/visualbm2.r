# rolling update beta and spread

library(zoo)
library(tseries)
library(RSQLite)
library(TTR)

source('util.r')

plotpair2 <- function (drv, left, right, tag, betafrom, startdate, enddate, beta, alpha, pvalue, hlife, smean, ssd, decay, upper, lower, hurstdb, scale.max, scale.min, scale.ratio, dotrd=FALSE, normalized=F, sprddetail=F, quantilebound=0.05, usersi=F, useacf=F)
{
    s.zoo = getquote(dbdrv, c(left, right), startdate, enddate)
    snames = names(s.zoo)

    ab = rollingbeta(s.zoo, 1400, 22)

    ab2 = zoo(matrix(rep(NA, NCOL(ab)), nrow=1), index(s.zoo))
    window(ab2, index=index(ab)) <- coredata(ab)
    window(ab2, index=start(ab2)) <- ab[1,]
    ab = na.locf(ab2)

    sprd = ab[,2:NCOL(ab)] * s.zoo[,2:NCOL(s.zoo)]
    sprd = apply(sprd, 1, sum)
    sprd = zoo(as.vector(sprd), index(s.zoo))
    sprd = s.zoo[,1] - sprd

    sprd2 <- apply(s.zoo, 1, function(x) {x[1] - sum(x[-1]*beta)})
    sprd2 <- zoo(as.vector(sprd2), index(s.zoo))

    newhlife = ouhlife(sprd)
    newpvalue = adf.test(as.vector(sprd), alternative="stationary")$p.value

    if (decay < 0) decay = round(hlife * -decay)

    emeanline <- ema(sprd, lambda=2.8854*decay)
    emean2line <- ema(sprd**2, lambda=2.8854*decay)
    esdline <- sqrt(emean2line - emeanline**2)

    s.zoo <- cbind(s.zoo, sprd=sprd)
    s.zoo <- cbind(s.zoo, sprd2=sprd2)

    s.zoo <- cbind(s.zoo, smean=smean)
    s.zoo <- cbind(s.zoo, ssd=ssd)
    s.zoo <- cbind(s.zoo, upper=(smean+ssd))
    s.zoo <- cbind(s.zoo, lower=(smean-ssd))
    s.zoo <- cbind(s.zoo, upper2=(smean+2*ssd))
    s.zoo <- cbind(s.zoo, lower2=(smean-2*ssd))

    s.zoo <- cbind(s.zoo, emean=emeanline)
    s.zoo <- cbind(s.zoo, esd=esdline)
    s.zoo <- cbind(s.zoo, eupper=(s.zoo$emean+s.zoo$esd))
    s.zoo <- cbind(s.zoo, elower=(s.zoo$emean-s.zoo$esd))
    s.zoo <- cbind(s.zoo, eupper2=(s.zoo$emean+2*s.zoo$esd))
    s.zoo <- cbind(s.zoo, elower2=(s.zoo$emean-2*s.zoo$esd))

    pdf(paste(left,paste(right,collapse='.'),tag,'pdf',sep='.'), width=17.55, height=8.3)

    #plot(ab)

    rb = ab[,seq(2, NCOL(ab))]
    modrb = rollapply(rb, 1, function(x){sqrt(sum(x*x))}, by.column=F)
    modbeta = sqrt(sum(beta*beta))
    diffbeta = rollapply(rb, 1, function(x){x-beta}, by.column=F)
    moddiff = rollapply(diffbeta, 1, function(x){sqrt(sum(x*x))}, by.column=F)
    dotbeta = rollapply(rb, 1, function(x){sum(x*beta)}, by.column=F)

    angle = acos(dotbeta/modrb/modbeta)/pi*180
    diffratio = moddiff/modbeta

    plot(rb)
    plot(angle)
    plot(diffratio)


    dev.off()
}

args <- commandArgs(TRUE)
Sys.setlocale(category = "LC_TIME", locale = "C")

if (length(args) < 1) stop('visualbm.r plan-file')

print(args)
plan <- read.table(args[1], row.names=1, sep='=', colClasses='character', strip.white=TRUE)

startdate = as.Date(plan['visualfrom', 1])
enddate = as.Date(plan['visualto', 1])
tag = plan['tag', 1]
decay = as.numeric(plan['decay', 1])
normalized = as.logical(plan['normalized', 1])
sprddetail = as.logical(plan['sprddetail', 1])
quantilebound = as.numeric(plan['quantilebound', 1])

drv = dbDriver('SQLite')
con <- dbConnect(drv, dbname = plan['cointdb', 1])

tovisual <- dbGetQuery(con, plan['visuallist', 1])
if (!is.na(plan['visualfile', 1]))
{
    visualfile <- read.table(plan['visualfile', 1], col.names='cpair', stringsAsFactors=F, colClasses='character', strip.white=TRUE)
    tovisual <- as.data.frame(union(tovisual, visualfile))
    names(tovisual) = 'cpair'
}

betafrom <- plan['betafrom', 1]

dotrd <- as.logical(plan['dotrd', 1])
upper.default <- as.numeric(plan['upper.default', 1])
lower.default <- as.numeric(plan['lower.default', 1])

usehurst = as.logical(plan['usehurst', 1])
if (usehurst) hurstdb = dbConnect(drv, dbname=plan['hurstdb', 1]) else hurstdb = NA
scale.max = as.integer(plan['scale.max', 1])
scale.min = as.integer(plan['scale.min', 1])
scale.ratio = as.integer(plan['scale.ratio', 1])

usersi = as.logical(plan['usersi', 1])
useacf = as.logical(plan['useacf', 1])

pttest <- dbReadTable(con, betafrom)
tovisual <- merge(tovisual, pttest, by='cpair', all=FALSE)
rownames(tovisual) <- tovisual$cpair

setwd(plan['dbdir', 1])
for (i in 1:nrow(tovisual))
{
    cpair <- tovisual[i,]$cpair
    tmp <- unlist(strsplit(cpair, "\\."))
    left <- tmp[1]
    right <- tmp[2:length(tmp)]

    print(c(i, cpair))
    beta = as.numeric(unlist(strsplit(tovisual[i,]$beta, ';')))
    #beta = rep(1, length(right)) / length(right)
    alpha <- as.numeric(tovisual[i,]$alpha)
    pvalue <- as.numeric(tovisual[i,]$pvalue)
    hlife <- as.numeric(tovisual[i,]$hlife)
    smean <- as.numeric(tovisual[i,]$smean)
    ssd <- as.numeric(tovisual[i,]$ssd)

    upper = upper.default
    lower = lower.default
    if (dotrd)
    {
        q = sprintf('select upper, lower from tradeparam where cpair="%s"', cpair)
        ul = dbGetQuery(con, q)
        if (nrow(ul) > 0)
        {
            upper = ul$upper
            lower = ul$lower
        }
    }

    plotpair2(drv, left, right, tag, betafrom, startdate, enddate, beta, alpha, pvalue, hlife, smean, ssd, decay, upper, lower, hurstdb, scale.max, scale.min, scale.ratio, dotrd, normalized, sprddetail, quantilebound, usersi, useacf)
}
if (usehurst) dbDisconnect(hurstdb)
dbDisconnect(con)
dbUnloadDriver(drv)
warnings()
