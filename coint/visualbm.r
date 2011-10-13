library(zoo)

ema <- function (x, lambda = 0.1, startup = 0, startup.as=0)
{
    # startup.as == 0 : calculate startup value from x
    # startup.as == 1 : use startup as startup value
    y = as.vector(x)
    if (lambda >= 1)
        lambda = 2/(lambda + 1)
    if (startup == 0)
        startup = floor(2/lambda)
    if (lambda == 0) {
        ema = rep(mean(x), length(x))
    }
    if (lambda > 0) {
        ylam = y * lambda
        if (startup.as == 0)
        {
            ylam[1] = mean(y[1:startup])
        }
        else
        {
            ylam[1] = startup*(1-lambda) + ylam[1]*lambda
        }
        ema = filter(ylam, filter = (1 - lambda), method = "rec")
    }
    x = as.vector(ema)
    x
}

plotpair <- function (left, right, beta, smean, ssd, emean, esd, decay)
{
# plot only out part

    s1 <- read.csv(paste(left,'out',sep='.'), stringsAsFactors=F)
    s1_date <- as.Date(as.character(s1$DATE), '%Y%m%d')

    s2 <- read.csv(paste(right,'out',sep='.'), stringsAsFactors=F)
    s2_date <- as.Date(as.character(s2$DATE), '%Y%m%d')

    s1 <- zoo(s1$PRECLOSE, s1_date)
    s2 <- zoo(s2$PRECLOSE, s2_date)

    s.zoo <- merge(s1, s2, all=FALSE)

    sprd <- s.zoo$s1 - beta*(s.zoo$s2)
    s.zoo <- cbind(s.zoo, sprd)
    upper <- smean + 1*ssd
    lower <- smean - 1*ssd

    emeanline <- ema(sprd, lambda=2.8854*decay, startup=emean, startup.as=1)
    emean2line <- ema(sprd**2, lambda=2.8854*decay, startup=(esd**2+emean**2), startup.as=1)
    esdline <- sqrt(emean2line - emeanline**2)

    eupper <- emeanline + 1*esdline
    elower <- emeanline - 1*esdline

    s.zoo <- cbind(s.zoo, upper=upper)
    s.zoo <- cbind(s.zoo, lower=lower)
    s.zoo <- cbind(s.zoo, smean=smean)
    s.zoo <- cbind(s.zoo, eupper=eupper)
    s.zoo <- cbind(s.zoo, elower=elower)
    s.zoo <- cbind(s.zoo, emean=emeanline)

    pdf(paste(left,right,'bm','pdf',sep='.'), width=11.7, height=8.3)
    ylim = c(min(lower, elower, sprd), max(upper, eupper, sprd))
    plot(ylim=ylim, sprd)
    lines(s.zoo$upper, col='red')
    lines(s.zoo$lower, col='red')
    lines(s.zoo$smean, col='red', type='p', pch='+')
    lines(s.zoo$eupper, col='blue')
    lines(s.zoo$elower, col='blue')
    lines(s.zoo$emean, col='blue', type='p', pch='*')
    dev.off()
}

plotpair2 <- function (left, right, beta, smean, ssd, emean, esd, decay)
{
# plot in+out

    s1 <- read.csv(paste(left,'in',sep='.'), stringsAsFactors=F)
    s1_date <- as.Date(as.character(s1$DATE), '%Y%m%d')

    s2 <- read.csv(paste(right,'in',sep='.'), stringsAsFactors=F)
    s2_date <- as.Date(as.character(s2$DATE), '%Y%m%d')

    s1 <- zoo(s1$PRECLOSE, s1_date)
    s2 <- zoo(s2$PRECLOSE, s2_date)

    s.zoo.in <- merge(s1, s2, all=FALSE)

    s1 <- read.csv(paste(left,'out',sep='.'), stringsAsFactors=F)
    s1_date <- as.Date(as.character(s1$DATE), '%Y%m%d')

    s2 <- read.csv(paste(right,'out',sep='.'), stringsAsFactors=F)
    s2_date <- as.Date(as.character(s2$DATE), '%Y%m%d')

    s1 <- zoo(s1$PRECLOSE, s1_date)
    s2 <- zoo(s2$PRECLOSE, s2_date)

    s.zoo.out <- merge(s1, s2, all=FALSE)

    s.zoo <- rbind(s.zoo.in, s.zoo.out)

    sprd <- s.zoo$s1 - beta*(s.zoo$s2)
    s.zoo <- cbind(s.zoo, sprd)
    upper <- smean + 1*ssd
    lower <- smean - 1*ssd

    emeanline <- ema(sprd, lambda=2.8854*decay)
    emean2line <- ema(sprd**2, lambda=2.8854*decay)
    esdline <- sqrt(emean2line - emeanline**2)

    eupper <- emeanline + 1*esdline
    elower <- emeanline - 1*esdline

    s.zoo <- cbind(s.zoo, upper=upper)
    s.zoo <- cbind(s.zoo, lower=lower)
    s.zoo <- cbind(s.zoo, smean=smean)
    s.zoo <- cbind(s.zoo, eupper=eupper)
    s.zoo <- cbind(s.zoo, elower=elower)
    s.zoo <- cbind(s.zoo, emean=emeanline)

    pdf(paste(left,right,'bm2','pdf',sep='.'), width=17.55, height=8.3)
    ylim = c(min(lower, elower, sprd), max(upper, eupper, sprd))
    plot(ylim=ylim, sprd)
    lines(s.zoo$upper, col='red')
    lines(s.zoo$lower, col='red')
    lines(s.zoo$smean, col='red', type='p', pch='+')
    lines(s.zoo$eupper, col='blue')
    lines(s.zoo$elower, col='blue')
    lines(s.zoo$emean, col='blue', type='p', pch='*')
    grid(lwd=2)
    dev.off()
}

args <- commandArgs(TRUE)
Sys.setlocale(category = "LC_ALL", locale = "C")

pttest <- read.csv(args[1], colClasses=c("character"))

setwd('data')
for (i in 1:nrow(pttest))
{
    cpair <- pttest[i,]$cpair
    npair <- pttest[i,]$npair
    beta <- as.numeric(pttest[i,]$beta)
    pvalue <- as.numeric(pttest[i,]$pvalue)
    smean <- as.numeric(pttest[i,]$smean)
    ssd <- as.numeric(pttest[i,]$ssd)
    emean <- as.numeric(pttest[i,]$emean360)
    esd <- as.numeric(pttest[i,]$esd360)

    if (pvalue < 0.06)
    {
        tmp <- unlist(strsplit(cpair, "\\."))
        left <- tmp[1]
        right <- tmp[2]
        print(c(left, right))

        plotpair2(left, right, beta, smean, ssd, emean, esd, 90*2)
    }
}
