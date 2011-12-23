# gen input sample files names
library(zoo)
library(tseries)
library(RSQLite)
library(gtools)#for combinaitons function

source('util.r')

coint.test <- function (dbdrv, left, right, startdate, enddate, beta=NA, alpha=NA)
{
    s.zoo = getquote(dbdrv, c(left, right), startdate, enddate)
    snames = names(s.zoo)

    beta_isext = TRUE
    if (is.na(beta)) {
        beta_isext = FALSE
        f = as.formula(paste(snames[1], '~', paste(snames[-1], collapse='+')))
        #print(f)
        m <- lm(f, data=s.zoo)
        #print(m)
        alpha <- coef(m)[1]
        beta <- coef(m)[-1]
        names(beta) <- paste('beta', right, sep='')
    }
    if (any(beta<0)) return(NA)

    sprd <- apply(s.zoo, 1, function(x) {x[1] - sum(x[-1]*beta)})

    ht <- adf.test(as.vector(sprd), alternative="stationary")

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
    print(c(i, s0, sa))
    if (is.null(betas)==T)
    {
        ret <- coint.test(drv, s0, sa, startdate, enddate)
    } else
    {
        cpair = paste(s0, paste(sa, collapse='.'), sep='.')
        beta = as.numeric(unlist(strsplit(betas[cpair,]$beta, ';')))
        alpha = betas[cpair,]$alpha
        ret <- coint.test(drv, s0, sa, startdate, enddate, beta, alpha)
    }
    if (!is.na(ret)) allret <- rbind(allret, ret)
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

#warnings()
#print(allret[order(allret[,4]),])
