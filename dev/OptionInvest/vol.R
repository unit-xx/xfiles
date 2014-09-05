library(fOptions)
library(ggplot2)

# for differrent vol values, compute and visualize option values.

X = 50
r = 0.05
t = 0.25
type = 'c'

Srng = seq(20, 80, 1)
volrng = seq(0.1, 0.5, 0.01)

# option price vs stock price, vary by vol
pdf('option.vol.pdf', width=17.55, height=11.07)

opval = expand.grid(S=Srng, vol=volrng)
valvec = rep(0, NROW(opval))
deltavec = rep(0, NROW(opval))
gammavec = rep(0, NROW(opval))
t1 = Sys.time()
for (i in 1:NROW(opval))
{
  tmp = opval[i,]
  S = tmp$S
  vol = tmp$vol
  
  val = GBSOption(type, S, X, t, r, r, vol)
  valvec[i] = val@price
  
  delta = GBSGreeks('delta', type, S, X, t, r, r, vol)
  deltavec[i] = delta
  
  gamma = GBSGreeks('gamma', type, S, X, t, r, r, vol)
  gammavec[i] = gamma
}
t2 = Sys.time()
print(t2-t1)
print((t2-t1)/NROW(opval))

opval = cbind(opval, val=valvec, delta=deltavec, gamma=gammavec)

a = ggplot(data=opval, aes(x=S,y=val,group=vol,col=vol)) + geom_line()+
  scale_colour_gradient(low="red") +
  geom_vline(xintercept = X)+
  labs(title='Option price vs Stock Price, vary by Vol')
print(a)

a = ggplot(data=opval, aes(x=S,y=delta,group=vol,col=vol)) + geom_line()+
  scale_colour_gradient(low="red") +
  geom_vline(xintercept = X)+
  labs(title='Delta vs Stock Price, vary by Vol')
print(a)

a = ggplot(data=opval, aes(x=S,y=gamma,group=vol,col=vol)) + geom_line()+
  scale_colour_gradient(low="red") +
  geom_vline(xintercept = X)+
  labs(title='Gamma vs Stock Price, vary by Vol')
print(a)

dev.off()

# t1 = Sys.time()
# for (i in 1:10000)
# {
# #  v = GBSOption(type, S, S*runif(1), t, r, r, vol)
#   v = GBSCharacteristics(type, S, S*runif(1), t, r, r, vol)
# }
# t2 = Sys.time()
# (t2-t1)/10000
#result: 0.000638036 secs per GBSOption
# 0.002177925 secs per GBSCharacteristics
