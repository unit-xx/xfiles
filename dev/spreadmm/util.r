ouhlife <- function(x)
{
  s = as.vector(x)
  ds = diff(s)
  smean= mean(s)
  s = s[-length(s)] - smean
  rst = lm(ds ~ s + 0)
  hlife = -log(2)/coef(rst)[1]
  hlife
}

read.quote <- function(qfn, trdstart='09:20:00', trdend='15:10:00')
{
  q1 = read.table(qfn, header=T, quote="\"", stringsAsFactors=F, 
                  colClasses=c('character','character','integer',
                               'character','numeric','numeric','numeric','numeric'))
  
  # dates and times series as zoo index
  dts = dates(q1$tradeday, format="ymd")
  tms = times(q1$tradetime, format='h:m:s')
  
  # trading hour
  tradeintval = which(tms > times(trdstart) & tms < times(trdend))
  
  tindex = as.POSIXct(paste(q1$tradeday, q1$tradetime), format="%Y%m%d %H:%M:%OS")
  
  q1.zoo = zoo(q1[,c(3,5,6,7,8)], tindex)
  q1.zoo = q1.zoo[tradeintval,]
  
  return(q1.zoo)
}

write.sprd <- function(sprdfn, sprd)
{
  write.zoo(sprd, file=sprdfn, index.name='Date Time', quote=F)
  # quote=F is very import
}

read.sprd <- function(sprdfn)
{
  sprd = read.zoo(sprdfn, index=list(1,2), FUN=paste, FUN2=as.POSIXct, 
                  sep=' ', header=T, stringsAsFactors=F)
  return(sprd)
}

mmperfsum <- function(ttrace, txcost, tidx)
{
  if(NROW(ttrace) < 1)
  {
    # no trade at all
    return(as.data.frame(list(tidx=tidx, ntrd=0, nshort=0, 
                              nlong=0, nmismatch=0, 
                              prft=0.0,
                              implcost=0.0)))
  }
  # ttrace: tick, longshort, sprd, day
  ntrd = max(which(ttrace$q==0))
  if (ntrd==-Inf) ntrd = 0 # the case when there's only one trade

  nmismatch = NROW(ttrace) - (ntrd)
  if(ntrd > 0)
  {
    tmp = ttrace[1:ntrd,]
    
    nshort = length(which(tmp$longshort==-1))
    nlong = length(which(tmp$longshort==1))
    prft = -sum(tmp$longshort * tmp$sprd) - txcost*ntrd
    implcost = -sum(tmp$longshort * tmp$sprd) / ntrd
    
    return(as.data.frame(list(tidx=tidx, ntrd=ntrd, nshort=nshort, 
                              nlong=nlong, nmismatch=nmismatch, 
                              prft=prft,
                              implcost=implcost)))
  }
  else
  {
    # ntrd == 0 here
    return(as.data.frame(list(tidx=tidx, ntrd=0, nshort=0, 
                              nlong=0, nmismatch=nmismatch, 
                              prft=0.0,
                              implcost=0.0)))
  }
}

# cc is the midline of dsprd$mid. dsprd has three components: mid, bid, ask
mmtrdbt <- function(dsprd, cc, tintns, sigadj)
{
  # (short) dsprd$bid-cc > (tintns+0.5*sigadj) - q*sigadj
  # (long) cc-dsprd$ask > (tintns+0.5*sigadj) + q*sigadj
  
  # 1. find short, change q, and delta_a, delta_b
  # 2. find long, change q, and delta_a, delta_b
  
  message(paste('begin function', Sys.time()))
  q = 0 # inventory
  w = 0 # wealth
  shortdelta = dsprd$bidsprd-cc
  longdelta = cc-dsprd$asksprd
  ttrace = data.frame(stringsAsFactors=F)
  lastick = 0
  message(paste('begin mm', Sys.time()))
  while(T)
  {
    #delta_a = (tintns+0.5*sigadj) - q*sigadj
    #delta_b = (tintns+0.5*sigadj) + q*sigadj
    delta_a = tintns + (0.5-q)*sigadj
    delta_b = tintns + (0.5+q)*sigadj
    
    #print(c(lastick, q, delta_a, delta_b))
    
    shorticks = which(shortdelta > delta_a)
    longticks = which(longdelta > delta_b)
    
    shorticks = shorticks[which(shorticks>lastick)]
    longticks = longticks[which(longticks>lastick)]
    
    shortick = shorticks[1]
    longtick = longticks[1]
    
    #shortick = shorticks[findInterval(lastick+1, shorticks)+1]
    #longtick = longticks[findInterval(lastick+1, longticks)+1]
    
    if(all(is.na(c(shortick, longtick))))
    {
      # clean up: some trades are not paired.
      break
    }
    
    if(FALSE==any(is.na(c(shortick, longtick))))
    {
      if(shortick < longtick)
      {
        # do short
        ttrace = rbind(ttrace, c(shortick, -1))
        q = q - 1
        lastick = shortick
      }
      else
      {
        # do long
        ttrace = rbind(ttrace, c(longtick, 1))
        q = q + 1
        lastick = longtick
      }
    }
    
    if(TRUE==any(is.na(c(shortick, longtick))))
      # all is NA case has been considered, so either shortick/longtick
      # is NA, but not both
    {
      if(is.na(shortick))
      {
        # do long
        ttrace = rbind(ttrace, c(longtick, 1))
        q = q + 1
        lastick = longtick
      }
      else
      {
        # do short
        ttrace = rbind(ttrace, c(shortick, -1))
        q = q - 1
        lastick = shortick
      }
    }
  }
  message(paste('end mm', Sys.time()))
  
  message(paste('begin making ttrace', Sys.time()))
  if(NROW(ttrace)>0)
  {
    names(ttrace) = c('tick', 'longshort')
    ttrace = cbind(ttrace, sprd=0)
    
    shortrd = which(ttrace$longshort==-1)
    shorticks = ttrace$tick[shortrd]
    ttrace$sprd[shortrd] = dsprd$bidsprd[shorticks]
    
    longtrd = which(ttrace$longshort==1)
    longticks = ttrace$tick[longtrd]
    ttrace$sprd[longtrd] = dsprd$asksprd[longticks]
    
    ttrace = cbind(ttrace, bidsprd=as.vector(dsprd$bidsprd[ttrace$tick]),
                   asksprd=as.vector(dsprd$asksprd[ttrace$tick]))
  }
  message(paste('end making ttrace', Sys.time()))
  message(paste('end function', Sys.time()))
  return(ttrace)
}

mmtrdbt2 <- function(dsprd, cc, tintns, sigadj)
{
  # (short) dsprd$bid-cc > (tintns+0.5*sigadj) - q*sigadj
  # (long) cc-dsprd$ask > (tintns+0.5*sigadj) + q*sigadj
  
  # 1. find short, change q, and delta_a, delta_b
  # 2. find long, change q, and delta_a, delta_b
  
  message(paste('begin function', Sys.time()))
  q = 0 # inventory
  w = 0 # wealth
  shortdelta = dsprd$bidsprd-cc
  longdelta = cc-dsprd$asksprd
  ttrace = data.frame(stringsAsFactors=F)
  lastick = 0
  ntick = NROW(dsprd$bidsprd)
  message(paste('begin mm', Sys.time()))
  while(T)
  {
    #delta_a = (tintns+0.5*sigadj) - q*sigadj
    #delta_b = (tintns+0.5*sigadj) + q*sigadj
    delta_a = tintns + (0.5-q)*sigadj
    delta_b = tintns + (0.5+q)*sigadj
    
    #print(c(lastick, q, delta_a, delta_b))
    
    shorticks = which(shortdelta[(lastick+1):ntick] > delta_a)
    longticks = which(longdelta[(lastick+1):ntick] > delta_b)
    
    #shorticks = shorticks[which(shorticks>lastick)]
    #longticks = longticks[which(longticks>lastick)]
    
    shortick = shorticks[1] + lastick
    longtick = longticks[1] + lastick
    
    #shortick = shorticks[findInterval(lastick+1, shorticks)+1]
    #longtick = longticks[findInterval(lastick+1, longticks)+1]
    
    totrd = which(!is.na(c(shortick, longtick)))
    
    if(length(totrd)==0)
    {
      break
    }
    else
    {
      if(length(totrd)==2)
      {
        if(shortick < longtick)
        {
          # do short
          ttrace = rbind(ttrace, c(shortick, -1))
          q = q - 1
          lastick = shortick
        }
        else
        {
          # do long
          ttrace = rbind(ttrace, c(longtick, 1))
          q = q + 1
          lastick = longtick
        }
      }
      else # only one choice: either short or long is possbile
      {
        if(totrd[1]==1)
        {
          # do short
          ttrace = rbind(ttrace, c(shortick, -1))
          q = q - 1
          lastick = shortick
        }
        else
        {
          # do long
          ttrace = rbind(ttrace, c(longtick, 1))
          q = q + 1
          lastick = longtick
        }
      }
    }
  }
  message(paste('end mm', Sys.time()))
  
  message(paste('begin making ttrace', Sys.time()))
  if(NROW(ttrace)>0)
  {
    names(ttrace) = c('tick', 'longshort')
    ttrace = cbind(ttrace, sprd=0)
    
    shortrd = which(ttrace$longshort==-1)
    shorticks = ttrace$tick[shortrd]
    ttrace$sprd[shortrd] = dsprd$bidsprd[shorticks]
    
    longtrd = which(ttrace$longshort==1)
    longticks = ttrace$tick[longtrd]
    ttrace$sprd[longtrd] = dsprd$asksprd[longticks]
    
    ttrace = cbind(ttrace, bidsprd=as.vector(dsprd$bidsprd[ttrace$tick]),
                   asksprd=as.vector(dsprd$asksprd[ttrace$tick]))
  }
  message(paste('end making ttrace', Sys.time()))
  message(paste('end function', Sys.time()))
  return(ttrace)
}

mmtrdbt3 <- function(dsprd, cc, tintns, sigadj, qmax)
{
  # (short) dsprd$bid-cc > (tintns+0.5*sigadj) - q*sigadj
  # (long) cc-dsprd$ask > (tintns+0.5*sigadj) + q*sigadj
  
  # 1. find short, change q, and delta_a, delta_b
  # 2. find long, change q, and delta_a, delta_b
  
  #message(paste('begin function', Sys.time()))
  q = 0 # inventory
  w = 0 # wealth
  shortdelta = dsprd$bidsprd-cc
  longdelta = cc-dsprd$asksprd
  ttrace = data.frame(stringsAsFactors=F)
  lastick = 0
  ntick = NROW(dsprd$bidsprd)
  q.da.cache = list()
  q.db.cache = list()
  
  #message(paste('begin mm', Sys.time()))
  while(T)
  {
    delta_a = tintns + (0.5-q)*sigadj
    delta_b = tintns + (0.5+q)*sigadj
    
    #print(c(lastick, q, delta_a, delta_b))
    
    if(as.character(q) %in% names(q.da.cache))
    {
      shorticks = q.da.cache[[as.character(q)]]
      longticks = q.db.cache[[as.character(q)]]
    }
    else
    {
      shorticks = which(shortdelta > delta_a+1e-6)
      longticks = which(longdelta > delta_b+1e-6)
      q.da.cache[[as.character(q)]] = shorticks
      q.db.cache[[as.character(q)]] = longticks
    }
    
    shortick = shorticks[findInterval(lastick, shorticks)+1]
    longtick = longticks[findInterval(lastick, longticks)+1]
    
    totrd = which(!is.na(c(shortick, longtick)))
    
    if(length(totrd)==0)
    {
      break
    }
    else
    {
      if(length(totrd)==2)
      {
        if(shortick < longtick)
        {
          # do short
          if(q > -qmax)
          {
            q = q - 1
            ttrace = rbind(ttrace, c(shortick, -1, q, delta_a, delta_b))
            lastick = shortick
          }
          else
          {
            # do long, because q reaches qmax and we cannot short any more.
            q = q + 1
            ttrace = rbind(ttrace, c(longtick, 1, q, delta_a, delta_b))
            lastick = longtick
          }
        }
        else
        {
          # do long
          if(q < qmax)
          {
            q = q + 1
            ttrace = rbind(ttrace, c(longtick, 1, q, delta_a, delta_b))
            lastick = longtick
          }
          else
          {
            # do short, because q reaches qmax and we cannot long any more.
            q = q - 1
            ttrace = rbind(ttrace, c(shortick, -1, q, delta_a, delta_b))
            lastick = shortick
          }
        }
      }
      else # only one choice: either short or long is possbile
      {
        if(totrd[1]==1)
        {
          # do short
          if(q > -qmax)
          {
            q = q - 1
            ttrace = rbind(ttrace, c(shortick, -1, q, delta_a, delta_b))
            lastick = shortick
          }
          else
          {
            # we cannot short because q reaches qmax, so only choice is break
            break
          }
        }
        else
        {
          # do long
          if(q < qmax)
          {
            q = q + 1
            ttrace = rbind(ttrace, c(longtick, 1, q, delta_a, delta_b))
            lastick = longtick
          }
          else
          {
            # we cannot long because q reaches qmax, so only choice is break
            break
          }
        }
      }
    }
  }
  #message(paste('end mm', Sys.time()))
  
  #message(paste('begin making ttrace', Sys.time()))
  if(NROW(ttrace)>0)
  {
    names(ttrace) = c('tick', 'longshort', 'q', 'delta_a', 'delta_b')
    ttrace$tick = index(dsprd)[ttrace$tick]
    ttrace = cbind(ttrace, sprd=0)
    
    shortrd = which(ttrace$longshort==-1)
    shorticks = ttrace$tick[shortrd]
    ttrace$sprd[shortrd] = dsprd$bidsprd[shorticks]
    
    longtrd = which(ttrace$longshort==1)
    longticks = ttrace$tick[longtrd]
    ttrace$sprd[longtrd] = dsprd$asksprd[longticks]
    
    ttrace = cbind(ttrace, bidsprd=as.vector(dsprd$bidsprd[ttrace$tick]),
                   asksprd=as.vector(dsprd$asksprd[ttrace$tick]),
                   cc=as.vector(cc[ttrace$tick]),
                   shortdelta=as.vector(shortdelta[ttrace$tick]),
                   longdelta=as.vector(longdelta[ttrace$tick]),
                   tintns=tintns, sigadj=sigadj, qmax=qmax
                   )
  }
  #message(paste('end making ttrace', Sys.time()))
  #message(paste('end function', Sys.time()))
  return(ttrace)
}

mmtrdbt4 <- function(dsprd, cc, tintns, sigadj, qmax)
{
  # cc is mid price
  # (short) dsprd$bid-cc > (tintns+0.5*sigadj) - q*sigadj
  # (long) cc-dsprd$ask > (tintns+0.5*sigadj) + q*sigadj
  
  # 1. find short, change q, and delta_a, delta_b
  # 2. find long, change q, and delta_a, delta_b
  
  #message(paste('begin function', Sys.time()))
  alltick = index(dsprd)
  allbids = coredata(dsprd$bidsprd)
  allasks = coredata(dsprd$asksprd)
  allcc = coredata(cc)
  shortdelta = coredata(dsprd$bidsprd-cc)
  longdelta = coredata(cc-dsprd$asksprd)
  
  o = which(!is.na(shortdelta))
  alltick = alltick[o]
  allbids = allbids[o]
  allasks = allasks[o]
  allcc = allcc[o]
  shortdelta = shortdelta[o]
  longdelta = longdelta[o]
  
  q = 0 # inventory
  ctick = 0
  NTICK = length(alltick)

  ttrace = data.frame(stringsAsFactors=F)
  optrace = rep(0, NTICK)
  qtrace = rep(0, NTICK)
  datrace = rep(0, NTICK)
  dbtrace = rep(0, NTICK)
  sprdtrace = rep(0, NTICK)
  
  # delta_b and delta_a are updated when q changes.
  delta_a = tintns + (0.5-q)*sigadj
  delta_b = tintns + (0.5+q)*sigadj

  while(ctick < NTICK)
  {
    ctick = ctick + 1

    # options: do short or long.
    if (shortdelta[ctick]>delta_a+1e-6 & q>-qmax)
    # do short
    {
      optrace[ctick] = -1
      q = q - 1
      qtrace[ctick] = q
      datrace[ctick] = delta_a
      dbtrace[ctick] = delta_b
      sprdtrace[ctick] = allbids[ctick]

      delta_a = tintns + (0.5-q)*sigadj
      delta_b = tintns + (0.5+q)*sigadj
    }

    if (longdelta[ctick]>delta_b+1e-6 & q<qmax)
    # do long
    {
      optrace[ctick] = 1
      q = q + 1
      qtrace[ctick] = q
      datrace[ctick] = delta_a
      dbtrace[ctick] = delta_b
      sprdtrace[ctick] = allasks[ctick]

      delta_a = tintns + (0.5-q)*sigadj
      delta_b = tintns + (0.5+q)*sigadj
    }
  }

  if(NROW(optrace)>0)
  {

    trades = which(optrace!=0)
    ttrace = as.data.frame(list(tick=alltick[trades],
                                longshort=optrace[trades],
                                q=qtrace[trades],
                                delta_a=datrace[trades],
                                delta_b=dbtrace[trades],
                                sprd=sprdtrace[trades],
                                bidsprd=allbids[trades],
                                asksprd=allasks[trades],
                                cc=allcc[trades],
                                shortdelta=shortdelta[trades],
                                longdelta=longdelta[trades],
                                tintns=tintns, sigadj=sigadj, qmax=qmax
                                ))

  }
  return(ttrace)
}

mmzjbt <- function(dq1, stopprofit, stoploss, oprice, cprice, daydir)
{
  ctick = 0
  NTICK = NROW(dq1)
  oprices = coredata(dq1[,oprice])
  cprices = coredata(dq1[,cprice])
  opticks = rep(0, NTICK) # where open/close happens
  otick = 0

  ttrace = data.frame(stringsAsFactors=F)
  
  while (ctick < NTICK)
  {
    ctick = ctick + 1

    # do open
    #print(paste('open', ctick))
    popen = oprices[ctick]
    otick = ctick
    
    
    #find close
    while (ctick < NTICK)
    {
      ctick = ctick + 1
      pclose = cprices[ctick]
      earning = daydir * (pclose - popen)
      if (earning>=stopprofit | earning<=stoploss)
      {
        opticks[otick] = daydir
        opticks[ctick] = -daydir
        break
      }
    }
  }
  #ttrace$tick = alltick[ttrace$tick,]
  ttrace = as.data.frame(list(tick=index(dq1)[which(opticks!=0)],
                              dir=opticks[which(opticks!=0)],
                              price=0.0
                                ))
  ttrace$price[which(ttrace$dir==daydir)] = oprices[which(opticks==daydir)]
  ttrace$price[which(ttrace$dir==-daydir)] = cprices[which(opticks==-daydir)]
  return(ttrace)
}

mmzjperfsum <- function(ttrace, txcost, day)
{
  ntrd = NROW(ttrace)
  prft = -sum(ttrace$dir * ttrace$price)
  prfttx = prft - txcost * ntrd
  return(as.data.frame(list(day=day, ntrd=ntrd, prft=prft, prfttx=prfttx)))
}

mmhftbt <- function(qday, mid, tintns, sigadj, qmax)
{
  
}

mmhftperf <- function(ttrace, txcost, day)
{
  
}

first.true <- function(op, vec, x, block=1024)
{
  #find first one in vector (vec), whose op(vec[i], x) is TRUE
  vvec = as.vector(vec)
  nvec = length(vvec)
  bidx = 1
  FUN = match.fun(op)
  while(bidx <= nvec)
  {
    vblock = vvec[bidx:min(bidx+block-1, nvec)]
    vret = which(FUN(vblock, x))[1]
    
    if(is.na(vret)==F) break
    
    bidx = bidx + block
  }
  return(vret+bidx-1)
}

vcos <- function(a, b)
{
  dotp = sum(a*b)
  alen = sqrt(sum(a*a))
  blen = sqrt(sum(b*b))
  return(dotp/alen/blen) 
}