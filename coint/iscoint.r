# gen input sample files names
library(zoo)
library(tseries)

ema <- function (x, lambda = 0.1, startup = 0)
{
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
        ylam[1] = mean(y[1:startup])
        ema = filter(ylam, filter = (1 - lambda), method = "rec")
    }
    x = as.vector(ema)
    x
}

coint.test <- function (left, right)
{
    s1 <- read.csv(paste(left,'in',sep='.'), stringsAsFactors=F)
    s1_date <- as.Date(as.character(s1$DATE), '%Y%m%d')

    s2 <- read.csv(paste(right,'in',sep='.'), stringsAsFactors=F)
    s2_date <- as.Date(as.character(s2$DATE), '%Y%m%d')

    left.name = s1$NAME[1]
    right.name = s2$NAME[1]
    s1 <- zoo(s1$PRECLOSE, s1_date)
    s2 <- zoo(s2$PRECLOSE, s2_date)

    s.zoo <- merge(s1, s2, all=FALSE)
#s.zoo <- window(s.zoo, start=as.Date('2008-01-01'))
    s <- as.data.frame(s.zoo)

    #cat("Date range is", format(start(s.zoo)), "to", format(end(s.zoo)), "\n")

    m <- lm(s$s1 ~ s$s2 + 0)#, data=s)
    beta <- coef(m)[1]

    #cat("Assumed hedge ratio is", beta, "\n")

    sprd <- s$s1 - beta*s$s2
    ht <- adf.test(sprd, alternative="stationary", k=0)

    #cat("ADF p-value is", ht$p.value, "\n")

    #if (ht$p.value < 0.05) {
    #    cat("The spread is likely mean-reverting\n")
    #} else {
    #    cat("The spread is not mean-reverting.\n")
    #}

    sprd <- s.zoo$s1-beta*s.zoo$s2
    smean <- mean(sprd)
    ssd <- sd(sprd)

    cc <- 2.8854

    emean90 <- tail(ema(sprd, lambda=cc*90),1)
    emean90sqr <- tail(ema(sprd**2, lambda=cc*90),1)
    esd90 <- sqrt(emean90sqr - emean90**2)

    emean180 <- tail(ema(sprd, lambda=cc*180),1)
    emean180sqr <- tail(ema(sprd**2, lambda=cc*180),1)
    esd180 <- sqrt(emean180sqr - emean180**2)

    emean270 <- tail(ema(sprd, lambda=cc*270),1)
    emean270sqr <- tail(ema(sprd**2, lambda=cc*270),1)
    esd270 <- sqrt(emean270sqr - emean270**2)

    emean360 <- tail(ema(sprd, lambda=cc*360),1)
    emean360sqr <- tail(ema(sprd**2, lambda=cc*360),1)
    esd360 <- sqrt(emean360sqr - emean360**2)

    info <- c(paste(left,right,sep='.'), paste(left.name, right.name, sep='.'), beta, ht$p.value, smean, ssd, emean90, esd90, emean180, esd180, emean270, esd270, emean360, esd360)
    #print(info)
    info
    #list(info=info,spread=sprd)
}

args <- commandArgs(TRUE)
print(args)
codes <- read.table(args[1], colClasses="character")#, fileEncoding='GB2312')
codes <- codes[,1]
#print(length(codes))
#print(codes)
setwd('data')
allret <- matrix(, nrow=0, ncol = 14, dimnames=list(c(),c('cpair', 'npair', 'beta', 'pvalue', 'smean', 'ssd', 'emean90', 'esd90', 'emean180', 'esd180', 'emean270', 'esd270', 'emean360', 'esd360')))
for (i in 1:(length(codes)-1))
{
    for (j in (i+1):length(codes))
    {
        ret <- coint.test(codes[i], codes[j])
        allret <- rbind(allret, ret)
    }
}
setwd('..')
#print(allret)
print(NROW(allret))
print(NCOL(allret))
write.csv(allret, file=args[2], row.names=FALSE)
#print(allret[order(allret[,4]),])

#pdf('09-13.pdf', width=11.7, height=8.3)
#plot(s.zoo$s1-beta*s.zoo$s2)
#dev.off()
