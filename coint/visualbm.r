library(zoo)
library(tseries)
library(RSQLite)

source('util.r')

plotpair2 <- function (drv, left, right, leftname, rightname, tag, betafrom, start, end, beta, pvalue, hlife, smean, ssd, decay)
{
# plot in+out
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
    s.zoo <- window(s.zoo, start=start, end=end)
    s <- as.data.frame(s.zoo)

    sprd <- s$s1 - beta*(s$s2)
    newhlife = ouhlife(sprd)
    newpvalue = adf.test(sprd, alternative="stationary", k=0)$p.value

    sprd <- s.zoo$s1 - beta*(s.zoo$s2)
    s.zoo <- cbind(s.zoo, sprd=sprd)

    # average lines from test result
    upper <- smean + 1*ssd
    lower <- smean - 1*ssd
    upper2 <- smean + 2*ssd
    lower2 <- smean - 2*ssd

    emeanline <- ema(sprd, lambda=2.8854*decay)
    emean2line <- ema(sprd**2, lambda=2.8854*decay)
    esdline <- sqrt(emean2line - emeanline**2)

    eupper <- emeanline + 1*esdline
    elower <- emeanline - 1*esdline
    eupper2 <- emeanline + 2*esdline
    elower2 <- emeanline - 2*esdline

    s.zoo <- cbind(s.zoo, smean=smean)
    s.zoo <- cbind(s.zoo, upper=upper)
    s.zoo <- cbind(s.zoo, lower=lower)
    s.zoo <- cbind(s.zoo, upper2=upper2)
    s.zoo <- cbind(s.zoo, lower2=lower2)

    s.zoo <- cbind(s.zoo, emean=emeanline)
    s.zoo <- cbind(s.zoo, eupper=eupper)
    s.zoo <- cbind(s.zoo, elower=elower)
    s.zoo <- cbind(s.zoo, eupper2=eupper2)
    s.zoo <- cbind(s.zoo, elower2=elower2)

    pdf(paste(left,right,tag,'pdf',sep='.'), width=17.55, height=8.3)
    ylim = c(min(lower2, elower2, sprd, na.rm=TRUE), max(upper2, eupper2, sprd, na.rm=TRUE))
    plot(ylim=ylim, sprd)
    lines(s.zoo$upper, col='red')
    lines(s.zoo$lower, col='red')
    lines(s.zoo$upper2, col='red')
    lines(s.zoo$lower2, col='red')
    lines(s.zoo$smean, col='red', type='p', pch='+')
    lines(s.zoo$eupper, col='blue')
    lines(s.zoo$elower, col='blue')
    lines(s.zoo$eupper2, col='blue')
    lines(s.zoo$elower2, col='blue')
    lines(s.zoo$emean, col='blue', type='p', pch='*')

    titlestr = sprintf('%s(in=%s) %s.%s.%s.%s beta=%.2f\nin.pvalue=%.2f in.hlife=%.2f\nout.pvalue=%.2f out.hlife=%.2f\ndecay=%d',
                        tag, betafrom,
                        left, right, leftname, rightname,
                        beta, pvalue, hlife, newpvalue, newhlife, decay)
    title(titlestr, family='song')

    abline(v=as.Date(unique(as.yearmon(index(s.zoo)))),
           h=seq(round(ylim[1],-2),round(ylim[2],-1),50),
           col='lightgrey',lty='dotted',lwd=1)

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

drv = dbDriver('SQLite')
con <- dbConnect(drv, dbname = plan['cointdb', 1])
tovisual <- dbGetQuery(con, plan['visuallist', 1])
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
    pvalue <- as.numeric(tovisual[i,]$pvalue)
    hlife <- as.numeric(tovisual[i,]$hlife)
    smean <- as.numeric(tovisual[i,]$smean)
    ssd <- as.numeric(tovisual[i,]$ssd)

    tmp <- unlist(strsplit(cpair, "\\."))
    left <- tmp[1]
    right <- tmp[2]
    npair <- iconv(npair, from='UTF-8', to='GBK')
    tmp <- unlist(strsplit(npair, "\\."))
    leftname <- tmp[1]
    rightname <- tmp[2]
    print(c(left, right))

    plotpair2(drv, left, right, leftname, rightname, tag, betafrom, startdate, enddate, beta, pvalue, hlife, smean, ssd, 22*6)
}
dbUnloadDriver(drv)
warnings()
