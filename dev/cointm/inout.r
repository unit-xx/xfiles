# a small script to view in/out pvalue and hlife relations

library(RSQLite)
library(lattice)

choiceN = 4
intbl = paste('large', choiceN, sep='')
outtbl = paste('small', choiceN, sep='')
dbfn = 'hs300index.db'
gfn = sprintf('hs3001v%d.pdf', choiceN)

drv = dbDriver('SQLite')
con = dbConnect(drv, dbfn)

q = sprintf('select a.cpair as cpair, a.pvalue as inpvalue, a.hlife as inhlife, b.pvalue as outpvalue, b.hlife as outhlife from %s a inner join %s b on (a.cpair=b.cpair) where inhlife < 300 and outhlife < 300 and inhlife > 0 and outhlife > 0', intbl, outtbl)
data = dbGetQuery(con, q)

pwidth = 17.55
pheight = 8.3
pdf(gfn, width=pwidth, height=pheight)

par(mfrow=c(1,2))

#a = which(data$inhlife > 0)
#b = which(data$inhlife < 200)
#c = which(data$outhlife > 0)
#d = which(data$outhlife < 200)
#
#all = intersect(a,b)
#all = intersect(all, c)
#all = intersect(all, d)
#data = data[all, ]

plot(data$inpvalue, data$inhlife, main='inpvalue-inhlife', type='p', pch='+')
plot(data$inpvalue, data$outpvalue, main='inpvalue-outpvalue', type='p', pch='+')
plot(data$inpvalue, data$outhlife, main='inpvalue-outhlife', type='p', pch='+')

plot(data$inhlife, data$outhlife, main='inhlife-outhlife', type='p', pch='+')
plot(data$inhlife, data$outpvalue, main='inhlife-outpvalue', type='p', pch='+')
plot(data$outpvalue, data$outhlife, main='outpvalue-outhlife', type='p', pch='+')

plot(density(data$inpvalue), main=paste('inpvalue-distributioin', mean(data$inpvalue), sd(data$inpvalue)))
plot(density(data$outpvalue), main=paste('outpvalue-distributioin', mean(data$outpvalue), sd(data$outpvalue)))

plot(density(data$inhlife), main=paste('inhlife-distributioin', mean(data$inhlife), sd(data$inhlife)))
plot(density(data$outhlife), main=paste('outhlife-distributioin', mean(data$outhlife), sd(data$outhlife)))

nx = 2
ny = 1
unit = min(pwidth/nx/1.3, pheight/ny/1.1)

gwidth = list(x=unit, unit='inches')
gheight = list(x=unit, unit='inches')

colorpal = terrain.colors(100, 1)
g <- cloud(outpvalue~inpvalue*inhlife, data=data, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),scales = list(arrows = FALSE), main='oupvalue', colorkey=list(space='left'), col.regions=colorpal)
plot(g, split=c(1,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=T)
g <- contourplot(outpvalue~inpvalue*inhlife, data=data, region=TRUE, cuts=15, scales = list(arrows = TRUE), colorkey=list(space='left'), col.regions=colorpal)
plot(g, split=c(2,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=F)

g <- cloud(outhlife~inpvalue*inhlife, data=data, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),scales = list(arrows = FALSE), main='outhlife', colorkey=list(space='left'), col.regions=colorpal)
plot(g, split=c(1,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=T)
g <- contourplot(outhlife~inpvalue*inhlife, data=data, region=TRUE, cuts=15, scales = list(arrows = TRUE), colorkey=list(space='left'), col.regions=colorpal)
plot(g, split=c(2,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=F)

dev.off()

dbDisconnect(con)
dbUnloadDriver(drv)

