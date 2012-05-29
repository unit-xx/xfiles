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

spreadbm <- function(spread, legquote, beta, upper, lower, dir=c('short','long','both'), longbcost=0.5/1000, longscost=1.5/1000, shortbcost=0.6/10000, shortscost=0.6/10000, shortmargin=2.5*1/6)
{
# spread is a data.frame/zoo object with 3 columns: $sprd, $mean, $sd.
# for simplicity, beta has the same number of columns as legquote and beta values are aligned in the same order as corresponding quote.
# upper/lower is in unit of sd.

    toopendir = match.arg(dir)
    toopendir = switch(toopendir, long=1, short=-1, both=0)
    ttrace = data.frame(stringsAsFactors=FALSE)

    opendir = 0
    tcost = 0
    holdcap = 0
    shortcap = 0
    longcap = 0
    shortindex = c()
    longindex = c()

    for (i in 1:nrow(spread))
    {
        p = spread[i,]
        sv = p$sprd
        mv = p$mean
        sdv = p$sd

        if (opendir == 0)
        {
            # looking for open
            if ((sv-mv)/sdv > upper && toopendir<=0) # deviation from mean is large enough and short is allowed.
            # open short
            {
                opendir = -1
                opent = index(p)
                shortindex = which(-beta < 0)
                longindex = which(-beta > 0)
                shortcap = sum(legquote[i,][,shortindex] * (-beta)[shortindex])
                longcap = sum(legquote[i,][,longindex] * (-beta)[longindex])
                holdcap = longcap + shortcap * shortmargin
                tcost = shortcap * shortscost + longcap * longbcost
            }

            if ((sv-mv)/sdv < -upper && toopendir>=0)
            # open long
            {
                opendir = 1
                opent = index(p)
                shortindex = which(beta < 0)
                longindex = which(beta > 0)
                shortcap = sum(legquote[i,][,shortindex] * (beta)[shortindex])
                longcap = sum(legquote[i,][,longindex] * (beta)[longindex])
                holdcap = longcap + shortcap * shortmargin
                tcost = shortcap * shortscost + longcap * longbcost
            }
        }
        else
        {
            # looking for close
            if ( ((opendir == -1) && ((sv-mv)/sdv < lower)) || ((opendir == 1) && ((sv-mv)/sdv > -lower)) )
            {
            # close short and long
                closet = index(p)
                if (opendir == -1)
                {
                    shortcap = sum(legquote[i,][,shortindex] * (-beta)[shortindex])
                    longcap = sum(legquote[i,][,longindex] * (-beta)[longindex])
                } else
                {
                    shortcap = sum(legquote[i,][,shortindex] * (beta)[shortindex])
                    longcap = sum(legquote[i,][,longindex] * (beta)[longindex])
                }

                tcost = tcost + shortcap * shortbcost + longcap * longscost
                earn = (as.numeric(spread[closet,]$sprd) - as.numeric(spread[opent,]$sprd)) * opendir - tcost

                ret = opendir * diff(window(spread$sprd, start=opent, end=closet))/holdcap
                maxdd = maxDrawdown(as.data.frame(ret), geometric=F)

                opensprd = spread[opent,]$sprd
                closesprd = spread[closet,]$sprd

                ttrace = rbind(ttrace, as.data.frame(list(opendir=opendir,
                                                       opensprd=opensprd, closesprd=closesprd,
                                                       holdcap=holdcap, maxdd=maxdd,
                                                       opent=opent, closet=closet,
                                                       earn=earn, tcost=tcost)))
                opendir = 0
                tcost = 0
                shortcap = 0
                longcap = 0
                holdcap = 0
                shortindex = c()
                longindex = c()
            }
        }
    }
    ttrace
}

nextbigger <- function(x, sortedseq, start)
{
# find the index in sortedseq that sortedseq[i]>x and i>=start
    nseq = length(sortedseq)
    i = start
    while(T)
    {
        if (i > nseq) { i = -1; break }
        if (sortedseq[i]>x) break else i = i + 1
    }
    i
}

matchtrade <-function(opens, exits)
{
# given possbile open and exit points, calculate matched open/close pairs
    oepair = data.frame()

    idopen = 1
    idexit = 1

    if (length(opens)==0 || length(exits)==0) return(oepair)

    while (T)
    {
        otick = opens[idopen]
        idexit = nextbigger(otick, exits, idexit)
        if (idexit==-1) break

        oepair = rbind(oepair, c(opens[idopen], exits[idexit]))

        etick = exits[idexit]
        idopen = nextbigger(etick, opens, idopen)
        if (idopen==-1) break
    }
    oepair
}

spreadbm2 <- function(spread, legquote, beta, upper, lower, dir=c('short','long','both'), longbcost=0.5/1000, longscost=1.5/1000, shortbcost=0.6/10000, shortscost=0.6/10000, shortmargin=2.5*1/6)
{
# spread is a data.frame/zoo object with 3 columns: $sprd, $mean, $sd.
# for simplicity, beta has the same number of columns as legquote and beta values are aligned in the same order as corresponding quote.
# upper/lower is in unit of sd.

    toopendir = match.arg(dir)
    toopendir = switch(toopendir, long=1, short=-1, both=0)
    ttrace = data.frame(stringsAsFactors=FALSE)
    oepair = data.frame()

    sprd = spread$sprd
    nsprd = (sprd-spread$mean)/spread$sd

    if (toopendir<=0)# seek for short opportunities
    {
        shorts = which(nsprd>upper)
        exits = which(nsprd<lower)
        shortoe = matchtrade(shorts, exits)
        if (NROW(shortoe) > 0) shortoe = cbind(shortoe, -1)
        oepair = rbind(oepair, shortoe)
    }

    if (toopendir>=0)# seek for long opportunities
    {
        longs = which(nsprd<-upper)
        exits = which(nsprd>-lower)
        longoe = matchtrade(longs, exits)
        if (NROW(longoe) > 0) longoe = cbind(longoe, 1)
        oepair = rbind(oepair, longoe)
    }

    if (NROW(oepair)==0) return(ttrace)

    oeorder = order(oepair[1])
    oepair = oepair[oeorder,] # sort by open ticks (first column)

    dates = index(sprd)
    allret = zoo(0, dates)
    for (i in 1:NROW(oepair))
    {
        opendir = oepair[i,][,3]
        otick = oepair[i,][,1]
        etick = oepair[i,][,2]
        opent = dates[otick]
        closet = dates[etick]
        opensprd = sprd[[otick]]
        closesprd = sprd[[etick]]

        tcost = 0
        holdcap = 0
        shortcap = 0
        longcap = 0

        if (opendir == -1) b = -beta

        shortindex = which(b<0)
        longindex = which(b>0)

        # open part
        shortcap = sum(legquote[otick,][,shortindex] * b[shortindex])
        longcap = sum(legquote[otick,][,longindex] * b[longindex])
        holdcap = longcap + shortcap * shortmargin
        tcost = shortcap * shortscost + longcap * longbcost

        # close part
        shortcap = sum(legquote[etick,][,shortindex] * b[shortindex])
        longcap = sum(legquote[etick,][,longindex] * b[longindex])
        tcost = tcost + shortcap * shortbcost + longcap * longscost
        earn = (closesprd - opensprd) * opendir - tcost

        ret = opendir * diff(window(sprd, start=opent, end=closet))/holdcap
        maxdd = maxDrawdown(as.data.frame(ret), geometric=F)

        window(allret, start=start(ret), end=end(ret)) <- coredata(ret)

        ttrace = rbind(ttrace, as.data.frame(list(opendir=opendir,
                                           opent=opent, closet=closet,
                                           opensprd=opensprd, closesprd=closesprd,
                                           holdcap=holdcap, maxdd=maxdd,
                                           earn=earn, tcost=tcost)))
    }
    if(NROW(ttrace)>0)
    {
        sharpeyear = sqrt(252)*mean(allret)/sd(allret)
        ttrace = cbind(ttrace, sharpeyear=sharpeyear)
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

    trelearn = 0.0
    avgrelearn = 0.0
    sdrelearn = 0.0

    tcost = 0.0
    avgcost = 0.0
    sdcost = 0.0

    ttxdur = 0.0
    avgtxdur = 0.0
    sdtxdur = 0.0

    maxdd = 0.0
    avgdd = 0.0
    sddd = 0.0

    sharpeyear = 0.0

    if (tcount > 0)
    {
        earns = as.vector(bmrst$earn)
        tearn = sum(earns)
        avgearn = mean(earns)
        sdearn = sd(earns)

        relearns = as.vector(bmrst$earn/bmrst$holdcap)
        trelearn = sum(relearns)
        avgrelearn = mean(relearns)
        sdrelearn = sd(relearns)

        cost = as.vector(bmrst$tcost)
        tcost = sum(cost)
        avgcost = mean(cost)
        sdcost = sd(cost)

        tduration = as.vector(bmrst$closet - bmrst$opent)
        ttxdur = as.numeric(sum(tduration))
        avgtxdur = as.numeric(mean(tduration))
        sdtxdur = as.numeric(sd(tduration))

        maxdds = as.vector(bmrst$maxdd)
        maxdd = max(maxdds)
        avgdd = mean(maxdds)
        sddd = sd(maxdds)

        sharpeyear = bmrst[1,]$sharpeyear
    }
    as.data.frame(list(tcount=tcount,
                       tearn=tearn, avgearn = avgearn, sdearn=sdearn,
                       trelearn=trelearn, avgrelearn = avgrelearn, sdrelearn=sdrelearn,
                       tcost=tcost, avgcost = avgcost, sdcost=sdcost,
                       ttxdur=ttxdur, avgtxdur=avgtxdur, sdtxdur=sdtxdur,
                       maxdd=maxdd, avgdd=avgdd, sddd=sddd,
                       sharpeyear=sharpeyear
                       ))
}

getquote <- function(dbdrv, codes, startdate, enddate, pricetag='close')
{
# return quotes as columns, and column names are 's'+codes

    left = codes[1]
    right = codes[-1]

    con <- dbConnect(drv, dbname = paste(left, 'db', sep='.'))
    s0 <- dbReadTable(con, 'data')
    dbDisconnect(con)
    Encoding(s0$name) = 'UTF-8'
    s0_date <- as.Date(as.character(s0$date), '%Y%m%d')
    s.zoo <- zoo(s0[,pricetag]*s0[,'factor'], s0_date)

    for(i in 1:length(right))
    {
        con <- dbConnect(drv, dbname = paste(right[i], 'db', sep='.'))
        sx <- dbReadTable(con, 'data')
        dbDisconnect(con)
        Encoding(sx$name) = 'UTF-8'
        sx_date <- as.Date(as.character(sx$date), '%Y%m%d')
        sx <- zoo(sx[,pricetag]*sx[,'factor'], sx_date)
        s.zoo <- merge(s.zoo, sx, all=FALSE)
    }

    s.zoo <- window(s.zoo, start=startdate, end=enddate)
    snames = c(paste('s',left,sep=''), paste('s',right,sep=''))
    names(s.zoo) <- snames
    s.zoo
}

fixstartbeta <- function(quote, bydates)
{
# beta is calculated by lm(left ~ right), as in getquote.
# bydates is a vector of dates.
    alphabeta = data.frame(stringsAsFactors=FALSE)
    snames = names(quote)
    f = as.formula(paste(snames[1], '~', paste(snames[-1], collapse='+')))

    for(i in 1:length(bydates))
    {
        q = window(quote, start=start(quote), end=bydates[i])
        m = lm(f, data=q)
        alphabeta = rbind(alphabeta, coef(m))
    }

    #alphabeta = rbind(alphabeta[1,], alphabeta)
    #alphabeta = zoo(alphabeta, c(start(quote), bydates))
    alphabeta = zoo(alphabeta, bydates)
    names(alphabeta) <- c('alpha', paste('beta', 1:(ncol(quote)-1), sep=''))
    alphabeta
    #b = rbind(zoo(as.matrix(b[1,]), start(s.zoo)), b)
}

rollingbeta <- function(quote, width, by)
{
    dolm<-function(q)
    {
        q2 = as.data.frame(q)
        snames = colnames(q2)
        f = as.formula(paste(snames[1], '~', paste(snames[-1], collapse='+')))
        m = lm(f, data=q2)
        coef(m)
    }

    alphabeta = rollapply(quote, width, dolm, by=by, by.column=F, align='right')    
    colnames(alphabeta) <- c('alpha', paste('beta', 1:(ncol(quote)-1), sep=''))
    alphabeta
}
