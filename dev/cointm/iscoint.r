# gen input sample files names
library(zoo)
library(tseries)
library(RSQLite)
library(gtools)#for combinaitons function

source('util.r')

coint.test <- function (dbdrv, left, right, startdate, enddate, beta=NA, alpha=NA)
{
    con <- dbConnect(drv, dbname = paste(left, 'db', sep='.'))
    s0 <- dbReadTable(con, 'data')
    dbDisconnect(con)
    Encoding(s0$name) = 'UTF-8'
    s0_date <- as.Date(as.character(s0$date), '%Y%m%d')
    s.zoo <- zoo(s0$close, s0_date)

    for(i in 1:length(right))
    {
        con <- dbConnect(drv, dbname = paste(right[i], 'db', sep='.'))
        sx <- dbReadTable(con, 'data')
        dbDisconnect(con)
        Encoding(sx$name) = 'UTF-8'
        sx_date <- as.Date(as.character(sx$date), '%Y%m%d')
        sx <- zoo(sx$close, sx_date)
        s.zoo <- merge(s.zoo, sx, all=FALSE)
    }

    s.zoo <- window(s.zoo, start=startdate, end=enddate)
    snames = c(paste('s',left,sep=''), paste('s',right,sep=''))
    names(s.zoo) <- snames

    #cat("Date range is", format(start(s.zoo)), "to", format(end(s.zoo)), "\n")

    beta_isext = TRUE
    if (is.na(beta))
    {
        beta_isext = FALSE
        f = as.formula(paste(snames[1], '~', paste(snames[-1], collapse='+')))
        #print(f)
        m <- lm(f, data=s.zoo)
        #print(m)
        alpha <- coef(m)[1]
        beta <- coef(m)[-1]
        names(beta) <- paste('beta', right, sep='')
    }

    #cat("Assumed hedge ratio is", beta, "\n")

    #sprd <- s.zoo$s1-beta1*s.zoo$s2-beta2*s.zoo$s3
    sprd <- apply(s.zoo, 1, function(x) {x[1] - sum(x[-1]*beta)})   #beta1*s$s2 - beta2*s$s3

    ht <- adf.test(as.vector(sprd), alternative="stationary")

    #cat("ADF p-value is", ht$p.value, "\n")

    #if (ht$p.value < 0.05) {
    #    cat("The spread is likely mean-reverting\n")
    #} else {
    #    cat("The spread is not mean-reverting.\n")
    #}

    smean <- mean(sprd)
    ssd <- sd(sprd)

    # calculate half-life time of reversion
    hlife = ouhlife(sprd)

    info <- as.data.frame(list(cpair=paste(left,paste(right,collapse='.'),sep='.'),
                               beta=paste(beta, collapse=';'),
                               alpha=alpha,
                               beta_isext=beta_isext,
                               pvalue=ht$p.value, 
                               hlife=hlife,
                               smean=smean,
                               ssd=ssd,
                               startdate=format(startdate),
                               enddate=format(enddate)),
                ,stringsAsFactors=FALSE)
    info
    #list(info=info,spread=sprd)
}

args <- commandArgs(TRUE)
if (length(args) < 1) {stop("iscoint plan-file")}

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
    betas = dbGetQuery(con, paste('select * from', plan['betafrom',1]))
    rownames(betas) <- betas$cpair
}
dbDisconnect(con)

setwd(plan['dbdir',1])

s0 = codes[1]
sas = codes[2:length(codes)]
tmode = plan['tmode', 1]
choiceN = as.integer(substr(tmode, 3, nchar(tmode)))
csa = combinations(length(sas), choiceN, v=sas)
for (i in 1:nrow(csa))
{
    sa = csa[i,]
    print(c(i, sa))
    if (is.null(betas)==T)
    {
        ret <- coint.test(drv, s0, sa, startdate, enddate)
    } else
    {
        cpair = paste(codes, collapse='.')
        beta = as.numeric(unlist(strsplit(betas[cpair,]$beta, ';')))
        alpha = betas[cpair,]$alpha
        ret <- coint.test(drv, s0, sa, startdate, enddate, beta, alpha)
    }
    allret <- rbind(allret, ret)
}

setwd('..')
print(NROW(allret))
print(NCOL(allret))

tag <- plan['tag',1]
con <- dbConnect(drv, plan['cointdb',1])
s1 <- dbWriteTable(con, paste(tag, choiceN, sep=''), allret, row.names=FALSE, overwrite=TRUE)
dbCommit(con)
dbDisconnect(con)
dbUnloadDriver(drv)

warnings()
#print(allret[order(allret[,4]),])
