ema <- function (x, lambda = 0.1, startup = 0, startup.as=0)
{
    # startup.as == 0 : calculate startup value from x
    # startup.as == 1 : use startup as startup value
    y = as.vector(x)
    if (lambda >= 1)
        lambda = 2/(lambda + 1)
    if (startup == 0)
        startup = floor(2/lambda/2.8854)
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

ouhlife <- function(spread)
{
    s = as.vector(spread)
    sp = s[2:length(s)]
    s = s[1:length(s)-1]
    ds = sp - s
    smean = mean(spread)
    s = s - smean
    rst = lm (ds ~ s + 0)
    hlife = -log(2)/coef(rst)[1];
    hlife
}

spreadbm <- function(spread, pair, upper, lower, decay=0, bcost=0.5/1000, scost=1.5/1000)
{
# decay==0 for static mean/sd, else for ema
# spread is a data.frame/zoo object with 1-column: spread value

    if (decay == 0)
    {
        meanline = mean(spread)
        sdline = sd(spread)
    }
    else
    {
        meanline = ema(spread, lambda = 2.8854*decay)
        mean2line = ema(spread**2, lambda = 2.8854*decay)
        sdline <- sqrt(mean2line - meanline**2)
    }

    s = cbind(spread, meanline, sdline)
    opendir = 0
    ttrace = data.frame(stringsAsFactors=FALSE)
    tcost = 0

    for (i in 1:nrow(s))
    {
        p = s[i,]
        sv = p[[1]]
        mv = p[[2]]
        sdv = p[[3]]
        if (opendir == 0)
        {
            # looking for open
            if ((sv-mv)/sdv > upper)
            # open short
            {
                opendir = -1
                opent = index(p)
                tcost = tcost + pair[i,][[1]]*scost + pair[i,][[2]]*bcost
            }

            if ((sv-mv)/sdv < -upper)
            # open long
            {
                opendir = 1
                opent = index(p)
                tcost = tcost + pair[i,][[1]]*bcost + pair[i,][[2]]*scost
            }
        }
        else
        {
            # looking for close
            if ((opendir == -1) && ((sv-mv)/sdv < lower))
            {
            # close short
                closet = index(p)
                tcost = tcost + pair[i,][[1]]*bcost + pair[i,][[2]]*scost
                earn = (s[closet,][[1]] - s[opent,][[1]]) * opendir - tcost

                ttrace = rbind(ttrace, as.data.frame(list(opendir=opendir,
                                                       opent=opent, closet=closet,
                                                       earn=earn, tcost=tcost)))
                opendir = 0
                tcost = 0
            }

            if ((opendir == 1) && ((sv-mv)/sdv > -lower))
            {
            # close short
                closet = index(p)
                tcost = tcost + pair[i,][[1]]*bcost + pair[i,][[2]]*scost
                earn = (s[closet,][[1]] - s[opent,][[1]]) * opendir - tcost
                ttrace = rbind(ttrace, as.data.frame(list(opendir=opendir,
                                                       opent=opent, closet=closet,
                                                       earn=earn, tcost=tcost)))
                opendir = 0
                tcost = 0
            }
        }
    }
    ttrace
}

bmstat <- function(bmrst)
{
# bmrst from spreadbm
# trade count, earning in total/avg/sd, max drawback, longest drawback time
    tcount = nrow(bmrst)
    tearn = 0.0
    avgearn = 0.0
    sdearn = 0.0

    tcost = 0.0
    avgcost = 0.0
    sdcost = 00

    ttxdur = 0.0
    avgtxdur = 0.0
    sdtxdur = 0.0
    if (tcount > 0)
    {
        earns = as.vector(bmrst$earn)
        tearn = sum(earns)
        avgearn = mean(earns)
        sdearn = sd(earns)

        cost = as.vector(bmrst$tcost)
        tcost = sum(cost)
        avgcost = mean(cost)
        sdcost = sd(cost)

        tduration = as.vector(bmrst$closet - bmrst$opent)
        ttxdur = as.numeric(sum(tduration))
        avgtxdur = as.numeric(mean(tduration))
        sdtxdur = as.numeric(sd(tduration))
    }
    as.data.frame(list(tcount=tcount,
                       tearn=tearn, avgearn = avgearn, sdearn=sdearn,
                       tcost=tcost, avgcost = avgcost, sdcost=sdcost,
                       ttxdur=ttxdur, avgtxdur=avgtxdur, sdtxdur=sdtxdur))
}

getquote <- function(dbdrv, codes, startdate, enddate, pricetag='close')
{
    left = codes[1]
    right = codes[-1]

    con <- dbConnect(drv, dbname = paste(left, 'db', sep='.'))
    s0 <- dbReadTable(con, 'data')
    dbDisconnect(con)
    Encoding(s0$name) = 'UTF-8'
    s0_date <- as.Date(as.character(s0$date), '%Y%m%d')
    s.zoo <- zoo(s0[,pricetag], s0_date)

    for(i in 1:length(right))
    {
        con <- dbConnect(drv, dbname = paste(right[i], 'db', sep='.'))
        sx <- dbReadTable(con, 'data')
        dbDisconnect(con)
        Encoding(sx$name) = 'UTF-8'
        sx_date <- as.Date(as.character(sx$date), '%Y%m%d')
        sx <- zoo(sx[,pricetag], sx_date)
        s.zoo <- merge(s.zoo, sx, all=FALSE)
    }

    s.zoo <- window(s.zoo, start=startdate, end=enddate)
    snames = c(paste('s',left,sep=''), paste('s',right,sep=''))
    names(s.zoo) <- snames
    s.zoo
}
