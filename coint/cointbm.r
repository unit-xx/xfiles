library(zoo)

bm <- function (left, right, beta, smean, ssd)
{
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
    print(c(upper,lower))

    tcount <- 0
    tcost <- 0
    tearn <- 0
    isopen <- 0
    osprd <- 0
    bcostr <- 0.0015
    scostr <- 0.0005

    for (i in 1:nrow(s.zoo))
    {
        sprdv <- s.zoo[i]$sprd[[1]]
        s1v <- s.zoo[i]$s1[[1]]
        s2v <- s.zoo[i]$s2[[1]]

        if (isopen == 0)
        {
            if (sprdv > upper)
            {
                isopen <- -1
                osprd <- sprdv
                tcount <- tcount + 1
                tcost <- tcost + s1v*scostr + s2v*beta*bcostr
            }else if (sprdv < lower)
            {
                isopen <- 1
                osprd <- sprdv
                tcount <- tcount + 1
                tcost <- tcost + s1v*bcostr + s2v*beta*scostr
            }
        }
        else
        {
            if (isopen == -1 && sprd < smean)
            {
                isopen <- 0
                tcost <- tcost + s1v*bcostr + s2v*beta*scostr
                tearn <- tearn + osprd - sprd
            }
            else if (isopen == 1 && sprd > smean)
            {
                isopen <- 0
                tcost <- tcost + s1v*scostr + s2v*beta*bcostr
                tearn <- tearn - osprd + sprd
            }
        }
    }
    ret <- c(format(start(s.zoo)), format(end(s.zoo)), tcount, tcost, tearn)
    ret
}

args <- commandArgs(TRUE)
pttest <- read.csv(args[1], colClasses=c("character"))

pttest <- pttest[which(as.numeric(pttest$pvalue) < 0.05),]

setwd('data')

bmstart <- c()
bmend <- c()
bmtcount <- c()
bmtcost <- c()
bmtearn <- c()

for (i in 1:nrow(pttest))
{
    cpair <- pttest[i,]$cpair
    npair <- pttest[i,]$npair
    beta <- as.numeric(pttest[i,]$beta)
    pvalue <- as.numeric(pttest[i,]$pvalue)
    smean <- as.numeric(pttest[i,]$smean)
    ssd <- as.numeric(pttest[i,]$ssd)
    smean2 <- as.numeric(pttest[i,]$smean2)
    ssd2 <- as.numeric(pttest[i,]$ssd2)

    tmp <- unlist(strsplit(cpair, "\\."))
    left <- tmp[1]
    right <- tmp[2]

    ret <- bm(left, right, beta, smean2, ssd2)
    bmstart <- rbind(bmstart, ret[1])
    bmend <- rbind(bmend, ret[2])
    bmtcount <- rbind(bmtcount, ret[3])
    bmtcost <- rbind(bmtcost, ret[4])
    bmtearn <- rbind(bmtearn, ret[5])
}

setwd('..')
pttest <- cbind(pttest, bmstart, bmend, bmtcount, bmtcost, bmtearn)
write.csv(pttest, file=args[2], row.names = FALSE)
