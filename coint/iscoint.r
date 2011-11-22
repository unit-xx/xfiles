# gen input sample files names
library(zoo)
library(tseries)
library(RSQLite)

source('util.r')

coint.test <- function (dbdrv, left, right, startdate, enddate, beta=NA, alpha=NA)
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

    left.name = s1$name[1]
    right.name = s2$name[1]
    s1 <- zoo(s1$close, s1_date)
    s2 <- zoo(s2$close, s2_date)

    s.zoo <- merge(s1, s2, all=FALSE)
    s.zoo <- window(s.zoo, start=startdate, end=enddate)
    s <- as.data.frame(s.zoo)

    #cat("Date range is", format(start(s.zoo)), "to", format(end(s.zoo)), "\n")

    beta_isext = TRUE
    if (is.na(beta))
    {
        beta_isext = FALSE
        m <- lm(as.vector(s$s1) ~ as.vector(s$s2))#, data=s)
        alpha <- coef(m)[1]
        beta <- coef(m)[2]
    }

    #cat("Assumed hedge ratio is", beta, "\n")

    sprd <- s$s1 - beta*s$s2
    ht <- adf.test(sprd, alternative="stationary")

    #cat("ADF p-value is", ht$p.value, "\n")

    #if (ht$p.value < 0.05) {
    #    cat("The spread is likely mean-reverting\n")
    #} else {
    #    cat("The spread is not mean-reverting.\n")
    #}

    sprd <- s.zoo$s1-beta*s.zoo$s2
    smean <- mean(sprd)
    ssd <- sd(sprd)

    # calculate half-life time of reversion
    hlife = ouhlife(sprd)

    info <- as.data.frame(list(cpair=paste(left,right,sep='.'),
                 npair=paste(left.name, right.name, sep='.'), 
                 beta=beta, alpha=alpha,
                 beta_isext=beta_isext,
                 pvalue=ht$p.value, 
                 hlife=hlife,
                 smean=smean,
                 ssd=ssd,
                 startdate=format(startdate),
                 enddate=format(enddate)),
                 stringsAsFactors=FALSE)
    info
    #list(info=info,spread=sprd)
}

args <- commandArgs(TRUE)
if (length(args) < 1) stop("iscoint plan-file")

print(args)
plan <- read.table(args[1], row.names=1, sep='=', colClasses='character', strip.white=TRUE)

codes <- read.table(plan['codefn',1], colClasses="character")
codes <- codes[,1]
allret <- data.frame(stringsAsFactors=FALSE)
startdate = as.Date(plan['testfrom',1])
enddate = as.Date(plan['testto',1])

drv = dbDriver('SQLite')
con <- dbConnect(drv, plan['cointdb',1])

betas = NULL
if (!is.na(plan['betafrom',1]))
{
    betas = dbGetQuery(con, paste('select cpair, beta, alpha from', plan['betafrom',1]))
    rownames(betas) <- betas$cpair
}
dbDisconnect(con)

setwd(plan['dbdir',1])
for (i in 1:(length(codes)-1))
{
    for (j in (i+1):length(codes))
    {
        print(c(codes[i], codes[j]))
        if (is.null(betas))
        {
            ret <- coint.test(drv, codes[i], codes[j], startdate, enddate)
        }
        else
        {
            cpair = paste(codes[i], codes[j], sep='.')
            beta = betas[cpair,]$beta
            alpha = betas[cpair,]$alpha
            ret <- coint.test(drv, codes[i], codes[j], startdate, enddate, beta, alpha)
        }
        allret <- rbind(allret, ret)
    }
}
setwd('..')
print(NROW(allret))
print(NCOL(allret))

tag <- plan['tag',1]
con <- dbConnect(drv, plan['cointdb',1])
s1 <- dbWriteTable(con, tag, allret, row.names=FALSE, overwrite=TRUE)
dbCommit(con)
dbDisconnect(con)
dbUnloadDriver(drv)

warnings()
#print(allret[order(allret[,4]),])
