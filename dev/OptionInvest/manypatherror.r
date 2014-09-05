library(fOptions)

source('callrep.r')

pdf('manyerror.pdf', width=17.55, height=11.07)

s0 = 100
dt = 0.001
T = 0.25
X = 100
u = 0.05
sig = 0.25
type = 'c'
pathnum = 2000

a = manypatherror(s0, dt, T, X, u, sig, type)

plot(a$ST, a$VT, pch='.')
points(a$ST, a$VT+a$error, col='red', pch='.')

plot(a$ST, a$VT, pch='.', xlim=c(80,120), ylim=c(-1,22))
points(a$ST, a$VT+a$error, col='red', pch='.')

plot(a$ST, a$error, pch='\'')

dev.off()
