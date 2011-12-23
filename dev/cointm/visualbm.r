library(zoo)
library(tseries)
library(RSQLite)
library(TTR)

source('util.r')

plotpair2 <- function (drv, left, right, tag, betafrom, startdate, enddate, beta, alpha, pvalue, hlife, smean, ssd, decay, upper, lower, hurstdb, scale.max, scale.min, scale.ratio, dotrd=FALSE, normalized=F, sprddetail=F, quantilebound=0.05, usersi=F, useacf=F)
{
    s.zoo = getquote(dbdrv, c(left, right), startdate, enddate)
    snames = names(s.zoo)

    sprd <- apply(s.zoo, 1, function(x) {x[1] - sum(x[-1]*beta)})
    sprd <- zoo(as.vector(sprd), index(s.zoo))
    s.zoo <- cbind(s.zoo, sprd=sprd)

    newhlife = ouhlife(sprd)
    newpvalue = adf.test(as.vector(sprd), alternative="stationary")$p.value

    if (decay < 0) decay = round(hlife * -decay)

    # moving average and sd line, i.e. Boilger line
    emeanline <- ema(sprd, lambda=2.8854*decay)
    emean2line <- ema(sprd**2, lambda=2.8854*decay)
    esdline <- sqrt(emean2line - emeanline**2)

    # rolling pvalue and hlife

    pvalueline = rollapplyr(s.zoo$sprd, hlife*2, function(x){adf.test(as.vector(x))$p.value}, by=hlife/2)
    hlifeline = rollapplyr(s.zoo$sprd, hlife*2, function(x){ouhlife(x)}, by=hlife/2)

    s.zoo <- cbind(s.zoo, pvalueline=pvalueline)
    s.zoo <- cbind(s.zoo, hlifeline=hlifeline)

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

    ylim = c(min(s.zoo$elower2, s.zoo$lower2, s.zoo$sprd, na.rm=TRUE), max(s.zoo$eupper2, s.zoo$upper2, s.zoo$sprd, na.rm=TRUE))
    plot(ylim=ylim, sprd, type='o', pch='-')
    lines(s.zoo$upper, col='red')
    lines(s.zoo$lower, col='red')
    lines(s.zoo$upper2, col='red')
    lines(s.zoo$lower2, col='red')
    lines(s.zoo$smean, col='red', type='p', pch='+')
    lines(s.zoo$eupper, col='blue', lty='dashed')
    lines(s.zoo$elower, col='blue', lty='dashed')
    lines(s.zoo$eupper2, col='blue', lty='dashed')
    lines(s.zoo$elower2, col='blue', lty='dashed')
    lines(s.zoo$emean, col='blue', type='p', pch='+')

    sprdunit = 50
    abline(v=as.Date(unique(as.yearmon(index(s.zoo)))),
           h=seq(round(ylim[1]-sprdunit,-2),round(ylim[2]+sprdunit,-2),sprdunit),
           col='grey',lty='dashed',lwd=1)

    titlestr = sprintf('%s(in=%s) %s.%s\nbeta=(%s) alpha=%.2f\nsprdutil=%.3f decay=%d\nin.pvalue=%.2f in.hlife=%.2f\nout.pvalue=%.2f out.hlife=%.2f',
                        tag, betafrom,
                        left, paste(right,collapse='.'),
                        paste(round(beta,2), collapse=';'), alpha,
                        ssd/hlife, decay,
                        pvalue, hlife, newpvalue, newhlife)

    if (dotrd)
    {
        bmrst = read.table(paste(left,paste(right,collapse='.'),tag,'trdbm',sep='.'), header=T, stringsAsFactors=F)
        for (i in 1:nrow(bmrst))
        {
            trd = bmrst[i,]
            x = as.Date(c(trd$opent, trd$closet))
            xy = sprd[x]
            color = ifelse((bmrst[i,]$opendir == 1), 'red', 'green')
            lines(xy, col=color, lwd=2)
        }
        titlestr = sprintf('%s\ntrades=%d upper=%.2f lower=%.2f\ntearns=%.2f trelearns=%.2f%%', titlestr, nrow(bmrst), upper, lower, sum(bmrst$earn), 100*sum(bmrst$earn/bmrst$holdcap))
    }

    if (usersi)
    {
        rsiline = RSI(sprd)
        s.zoo = cbind(s.zoo, rsi=rsiline)
        par(new=T)
        plot(s.zoo$rsi, col=colors()[258], axes=F, xlab='', ylab='', lty='dotdash')
        axis(4, col.axis='black', col='black', padj=-4)
    }

    # add hurst exponent
    if (!is.na(hurstdb))
    {
        tbname = paste('hurst', cpair, scale.max, scale.min, scale.ratio, sep='.')
        if (dbExistsTable(hurstdb, tbname))
        {
            hline = dbReadTable(hurstdb, paste('[', tbname, ']', sep=''))
            hline = window(zoo(hline$h, as.Date(hline$date, '%Y-%m-%d')), start=startdate, end=enddate)
            havg = ema(hline, lambda=2.8854*hlife)
            havg = zoo(havg, index(hline))
            s.zoo = cbind(s.zoo, hmean=havg)
            s.zoo = cbind(s.zoo, hurst=hline)

            par(new=TRUE)
            #plot(s.zoo$hurst, col='green', axes=F, bty='c', xlab='', ylab='')
            plot(s.zoo$hmean, col=colors()[96], axes=F, bty='c', xlab='', ylab='')
            axis(4, col.axis='black', col='black')
        }
    }

    title(titlestr, family='song', line=-4)

    plot(pvalueline, col='blue')
    par(new=T)
    plot(hlifeline, col='green', axes=F, bty='c', xlab='', ylab='', ylim=c(-300, 300))
    axis(4, col.axis='black', col='black')
    abline(v=as.Date(unique(as.yearmon(index(s.zoo)))),
           col='grey',lty='dashed',lwd=1)

    if (useacf) acf((as.vector(sprd)), lag.max=600, na.action=na.pass)

    if (sprddetail)
    {
        probs = c(quantilebound, 1-quantilebound)

        # spread density
        #q = quantile(sprd, probs=probs)
        #plot(density(sprd), main=sprintf('raw spread mean: %.2f, sd: %.2f, %d%% quantile (%.2f, %.2f)', round(mean(sprd),3), round(sd(sprd),3), quantilebound*100, q[1], q[2]))
        #abline(v=q)

        # spread diff, barplot and density
        rrate = diff((sprd))
        #q = quantile(rrate, probs=probs)
        #barplot(rrate, main=sprintf('spread diff mean: %.2f, sd: %.2f, %d%% quantile (%.2f, %.2f)', round(mean(rrate),3), round(sd(rrate),3), quantilebound*100, q[1], q[2]))
        #abline(v=as.Date(unique(as.yearmon(index(rrate)))), h=q)

        #plot(density(rrate), main=sprintf('spread diff mean: %.2f, sd: %.2f, %d%% quantile (%.2f, %.2f)', round(mean(rrate),3), round(sd(rrate),3), quantilebound*100, q[1], q[2]))
        #abline(v=q)

        # spread diff, its signs and absolute values
        #rsign = sign(rrate)
        #rvalue = abs(rrate)
        #q = quantile(rvalue, probs=probs)
        #toosmall = which(rvalue < q[1])
        #toolarge = which(rvalue > q[2])
        #rsign[toosmall] = 0
        #rsign[toolarge] = 0
        #plot(cumsum(rsign), main="up/down indicator")
        #abline(v=as.Date(unique(as.yearmon(index(rsign)))), col='grey',lty='dashed',lwd=1)
        #acf(cumsum(as.vector(rsign)), lag.max=600, na.action=na.pass)

        #barplot(rvalue, main=sprintf('spread diff absvalue mean: %.2f, sd: %.2f, %d%% quantile (%.2f, %.2f)', round(mean(rvalue),3), round(sd(rvalue),3), quantilebound*100, q[1], q[2]))
        #abline(v=as.Date(unique(as.yearmon(index(rvalue)))), h=q)

        #plot(hist(rvalue, plot=F), main=sprintf('spread diff absvalue mean: %.2f, sd: %.2f, %d%% quantile (%.2f, %.2f)', round(mean(rvalue),3), round(sd(rvalue),3), quantilebound*100, q[1], q[2]))
        #abline(v=q)

    }

    if (normalized)
    {
        nsprd = (s.zoo$sprd-s.zoo$emean)/s.zoo$esd
        ylim = c(min(nsprd), max(nsprd))
        plot(ylim=ylim, nsprd, type='o', pch='-', main='normalized spread view')
        sprdunit = 0.2
        abline(v=as.Date(unique(as.yearmon(index(s.zoo)))),
               h=seq(round(ylim[1]-sprdunit,0),round(ylim[2]+sprdunit,0),sprdunit),
               col='grey',lty='dashed',lwd=1)
        if (dotrd)
        {
            for (i in 1:nrow(bmrst))
            {
                trd = bmrst[i,]
                x = as.Date(c(trd$opent, trd$closet))
                xy = nsprd[x]
                color = ifelse((bmrst[i,]$opendir == 1), 'red', 'green')
                lines(xy, col=color, lwd=2)
            }
        }
        if (sprddetail)
        {
            rrate = diff((nsprd))
            barplot(rrate, main='normalized spread diff')
            plot(density(rrate), main=paste('normalized spread diff', round(mean(rrate),3), round(sd(rrate),3)))
        }
        if (useacf) acf((as.vector(nsprd)), lag.max=600, na.action=na.pass)
    }

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
