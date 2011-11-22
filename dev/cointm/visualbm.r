library(zoo)
library(tseries)
library(RSQLite)

source('util.r')

plotpair2 <- function (drv, left, right, tag, betafrom, startdate, enddate, beta, alpha, pvalue, hlife, smean, ssd, decay, upper, lower, dotrd=FALSE)
{
    con <- dbConnect(drv, dbname = paste(left, 'db', sep='.'))
    s0 <- dbReadTable(con, 'data')
    dbDisconnect(con)
    s0_date <- as.Date(as.character(s0$date), '%Y%m%d')
    s.zoo <- zoo(s0$close, s0_date)

    for(i in 1:length(right))
    {
        con <- dbConnect(drv, dbname = paste(right[i], 'db', sep='.'))
        sx <- dbReadTable(con, 'data')
        dbDisconnect(con)
        sx_date <- as.Date(as.character(sx$date), '%Y%m%d')
        sx <- zoo(sx$close, sx_date)
        s.zoo <- merge(s.zoo, sx, all=FALSE)
    }

    s.zoo <- window(s.zoo, start=startdate, end=enddate)
    snames = c(paste('s',left,sep=''), paste('s',right,sep=''))
    names(s.zoo) <- snames

    sprd <- apply(s.zoo, 1, function(x) {x[1] - sum(x[-1]*beta)})
    sprd <- zoo(as.vector(sprd), index(s.zoo))

    newhlife = ouhlife(sprd)
    newpvalue = adf.test(as.vector(sprd), alternative="stationary")$p.value

    # average lines from test result
    upperline <- smean + 1*ssd
    lowerline <- smean - 1*ssd
    upper2line <- smean + 2*ssd
    lower2line <- smean - 2*ssd

    emeanline <- ema(sprd, lambda=2.8854*decay)
    emean2line <- ema(sprd**2, lambda=2.8854*decay)
    esdline <- sqrt(emean2line - emeanline**2)

    eupper <- emeanline + 1*esdline
    elower <- emeanline - 1*esdline
    eupper2 <- emeanline + 2*esdline
    elower2 <- emeanline - 2*esdline

    s.zoo <- cbind(s.zoo, smean=smean)
    s.zoo <- cbind(s.zoo, upper=upperline)
    s.zoo <- cbind(s.zoo, lower=lowerline)
    s.zoo <- cbind(s.zoo, upper2=upper2line)
    s.zoo <- cbind(s.zoo, lower2=lower2line)

    s.zoo <- cbind(s.zoo, emean=emeanline)
    s.zoo <- cbind(s.zoo, eupper=eupper)
    s.zoo <- cbind(s.zoo, elower=elower)
    s.zoo <- cbind(s.zoo, eupper2=eupper2)
    s.zoo <- cbind(s.zoo, elower2=elower2)

    pdf(paste(left,paste(right,collapse='.'),tag,'pdf',sep='.'), width=17.55, height=8.3)

    ylim = c(min(lower2line, elower2, sprd, na.rm=TRUE), max(upper2line, eupper2, sprd, na.rm=TRUE))
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

    if (dotrd)
    {
        bmrst = spreadbm(sprd, s.zoo, upper, lower, decay)
        for (i in 1:nrow(bmrst))
        {
            x = bmrst[i,][,c(2,3)]
            xy = sprd[x]
            color = ifelse((bmrst[i,]$opendir == 1), 'red', 'green')
            lines(xy, col=color, lwd=2)
        }
    }

    titlestr = sprintf('%s(in=%s) %s.%s\nbeta=(%s)\nalpha=%.2f decay=%d\nin.pvalue=%.2f in.hlife=%.2f\nout.pvalue=%.2f out.hlife=%.2f',
                        tag, betafrom,
                        left, paste(right,collapse='.'),
                        paste(round(beta,2), collapse=';'),
                        alpha, decay,
                        pvalue, hlife, newpvalue, newhlife)

    if (dotrd)
    {
        titlestr = sprintf('%s\ntrades=%d upper=%.2f lower=%.2f', titlestr, nrow(bmrst), upper, lower)
    }
    title(titlestr, family='song', line=-2)

    abline(v=as.Date(unique(as.yearmon(index(s.zoo)))),
           h=seq(round(ylim[1],-2),round(ylim[2],-1),50),
           col='lightgrey',lty='dotted',lwd=1)

    # Hurst exponet using DFA
    #hexp <- rollapply(sprd, 132, function(z){DFA(z)[[1]]}, by=5, align = "right")
    #par(new=TRUE)
    #plot(hexp, col='green', axes=FALSE, bty='c', xlab='', ylab='')
    #axis(4, col.axis='black', col='black')
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

drv = dbDriver('SQLite')
con <- dbConnect(drv, dbname = plan['cointdb', 1])

tovisual <- dbGetQuery(con, plan['visuallist', 1])
betafrom <- plan['betafrom', 1]
tmode = plan['tmode', 1]
choiceN = as.integer(substr(tmode, 3, nchar(tmode)))

dotrd <- as.logical(plan['dotrd', 1])
upper.default <- as.numeric(plan['upper.default', 1])
lower.default <- as.numeric(plan['lower.default', 1])

pttest <- dbReadTable(con, paste(betafrom, choiceN, sep=''))
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

    plotpair2(drv, left, right, tag, betafrom, startdate, enddate, beta, alpha, pvalue, hlife, smean, ssd, decay, upper, lower, dotrd)
}
dbDisconnect(con)
dbUnloadDriver(drv)
warnings()
