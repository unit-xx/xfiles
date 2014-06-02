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
              cumcosttotal=cumcosttotal))
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


