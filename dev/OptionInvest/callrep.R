library(fOptions)

callrep <- function(tt, ss, delta, r, base=100)
{
  N = length(tt)
  
  sharetobuy = rep(0, N)
  costtobuy = rep(0, N)
  cumcosttobuy = rep(0, N)
  intrstcost = rep(0, N)
  cumintrst = rep(0, N)
  cumcosttotal = rep(0, N)
  
  sharetobuy = diff(delta) * base
  sharetobuy = c(delta[1]*base, sharetobuy)
  
  totalsharebought = delta * base
  
  totalsharevalue = totalsharebought * ss
  
  costtobuy = sharetobuy * ss
  
  cumcosttobuy = cumsum(costtobuy)
  
  intrstcost = diff(tt) * cumcosttobuy[-N] * r
  intrstcost = c(0, intrstcost)
  
  cumintrst = cumsum(intrstcost)
  
  cumcosttotal = cumcosttobuy + cumintrst
  
  return(list(sharetobuy=sharetobuy,
              costtobuy=costtobuy,
              cumcosttobuy=cumcosttobuy,
              intrstcost=intrstcost,
              cumintrst=cumintrst,
              cumcosttotal=cumcosttotal,
              totalsharebought=totalsharebought,
              totalsharevalue=totalsharevalue
              ))
}

test <- function()
{
  tt = 0.3846/20*(0:20)
  ss = c(49.00,
         48.12,
         47.37,
         50.25,
         51.75,
         53.12,
         53.00,
         51.87,
         51.38,
         53.00,
         49.88,
         48.50,
         49.88,
         50.37,
         52.13,
         51.88,
         52.87,
         54.87,
         54.62,
         55.87,
         57.25
         )
  
  delta = c(522,
            458,
            400,
            596,
            693,
            774,
            771,
            706,
            674,
            787,
            550,
            413,
            542,
            591,
            768,
            759,
            865,
            978,
            990,
            1000,
            1000)/1000
  
  a = callrep(tt,ss,delta, 0.05, 100000)
}

cashpath <-function(c0, u, tt)
{
  return (c0 * exp(u*tt))
}

lognormpath <- function(s0, u, sig, dt, N)
{
  # returns: a list
  # $t 
  # $st
}

deltapath <- function(tt, ss, type, X, u, sig, T)
{
  # return:
  # delta array
  deltas = rep(0, length(tt))
  for(i in 1:length(tt))
  {
    delta = GBSGreeks('delta', type, ss[i], X, (T-tt[i]), u, u, sig)
    deltas[i] = delta
  }
}

Vpath <- function(tt, ss, type, X, u, sig, T)
{
  # return:
  # options value array
  values = rep(0, length(tt))
  for(i in 1:length(tt))
  {
    value = GBSOption(type, ss[i], X, (T-tt[i]), u, u, sig)@price
    values[i] = value
  }
}

onepatherror <- function(tt, ss, type, X, u, sig, T)
{
  # replication error at every step of one path
  delta = deltapath(tt, ss, type, X, u, sig, T)
  rep = callrep(tt, ss, delta, u, base=100)
  realvalues = Vpath(tt, ss, type, X, u, sig, T)
  
  cpath = cashpath(v0, u, tt)
  
  repvalues = rep$cumcosttotal + rep$totalsharevalue + cpath
  
  error = repvalues - realvalues
  
  return(error)
}

manypatherror <- function()
{
  # replication error at the final step of many paths
  
  # replication many paths
  epath = onepatherror(tt, ss, type, X, u, sig, T)
  
  error = epath[length(epath)]
  finals = ss[length(ss)]
  
  
}

