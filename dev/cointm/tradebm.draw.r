# tradebm.r only gives trade result, this script shows how earning grows dynamically

library(zoo)
library(RSQLite)

source('util.r')

# given a pair and its beta, trade benchmarking using upper/lower bound params,
# and draw the returns figure

pairbm.draw <- function (dbdrv, tag, left, right, startdate, enddate, betafrom, beta, smean, ssd, upper, lower, hlife, decay, staticparam)
{
    s.zoo = getquote(dbdrv, c(left, right), as.Date(startdate), as.Date(enddate))
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

    emeanline <- ema(sprd, lambda=2.8854*decay)
    emean2line <- ema(sprd**2, lambda=2.8854*decay)
    esdline <- sqrt(emean2line - emeanline**2)
    s.zoo <- cbind(s.zoo, emean=emeanline)
    s.zoo <- cbind(s.zoo, esd=esdline)

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

    # add volatility line

    rrate = diff(sprd)/sprd
    vmeanline <- ema(rrate, lambda=2.8854*decay)
    vmean2line <- ema(rrate**2, lambda=2.8854*decay)
    vsdline <- sqrt(vmean2line - vmeanline**2)
    vsdline <- c(0, vsdline)
    s.zoo = cbind(s.zoo, vol=vsdline)
    #par(new=T)
    plot(s.zoo$vol, col=colors()[258], axes=F, xlab='', ylab='', lty='dotdash', type='o', pch='+')
    axis(4, col.axis='black', col='black', padj=-4)

    title('Relative Returns (with Tx cost)')
    titlestr = sprintf('%s(in=%s) %s.%s\nstart=%s end=%s\nsmean=%.2f ssd=%.2f\nupper=%.2f lower=%.2f using %s\nabs.Txcost=%.2f rel.Txcost=%.2f\nabs.ret=%.2f rel.ret=%.4f',
                        tag, betafrom,
                        left, paste(right,collapse='.'),
                        startdate, enddate,
                        smean, ssd,
                        upper, lower, switch(as.numeric(staticparam)+1, 'dynamicparam', 'staticparam'),
                        abscost, relcost,
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
trdstatfn = paste(tag, format(startdate, format='%Y%m%d'), format(enddate, format='%Y%m%d'), 'trdstat',sep='.')

drv = dbDriver('SQLite')

setwd(plan['dbdir', 1])
trdstat = read.table(trdstatfn, header=T, stringsAsFactors=F)
for (i in 1:NROW(trdstat))
{
    cpair = trdstat[i,]$cpair

    tmp <- unlist(strsplit(cpair, "\\."))
    left <- tmp[1]
    right <- tmp[2:length(tmp)]

    betafrom = trdstat[i,]$betafrom
    beta = as.numeric(unlist(strsplit(trdstat[i,]$beta, ';')))
    smean = trdstat[i,]$smean
    ssd = trdstat[i,]$ssd
    upper = trdstat[i,]$upper
    lower = trdstat[i,]$lower
    hlife = trdstat[i,]$hlife
    decay = trdstat[i,]$decay
    startdate = trdstat[i,]$startdate
    enddate = trdstat[i,]$enddate
    staticparam = trdstat[i,]$staticparam

    print(c(i, cpair))

    pairbm.draw(drv, tag, left, right, startdate, enddate, betafrom, beta, smean, ssd, upper, lower, hlife, decay, staticparam)
}
dbUnloadDriver(drv)
warnings()

