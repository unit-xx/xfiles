# a small script to view in/out pvalue and hlife relations

library(RSQLite)

choiceN = 4
intbl = paste('large', choiceN, sep='')
outtbl = paste('small', choiceN, sep='')
dbfn = 'hs300index.db'
gfn = sprintf('hs3001v%d.pdf', choiceN)

drv = dbDriver('SQLite')
con = dbConnect(drv, dbfn)

q = sprintf('select a.cpair as cpair, a.pvalue as inpvalue, a.hlife as inhlife, b.pvalue as outpvalue, b.hlife as outhlife from %s a inner join %s b on (a.cpair=b.cpair)', intbl, outtbl)
data = dbGetQuery(con, q)

pdf(gfn, width=17.55, height=8.3)

par(mfrow=c(1,2))

a = which(data$inhlife > 0)
b = which(data$inhlife < 200)
c = which(data$outhlife > 0)
d = which(data$outhlife < 200)

all = intersect(a,b)
all = intersect(all, c)
all = intersect(all, d)
data = data[all, ]

plot(data$inpvalue, data$inhlife, main='inpvalue-inhlife', type='p', pch='+')
plot(data$inpvalue, data$outpvalue, main='inpvalue-outpvalue', type='p', pch='+')
plot(data$inpvalue, data$outhlife, main='inpvalue-outhlife', type='p', pch='+')

plot(data$inhlife, data$outhlife, main='inhlife-outhlife', type='p', pch='+')
plot(data$inhlife, data$outpvalue, main='inhlife-outpvalue', type='p', pch='+')
plot(data$outpvalue, data$outhlife, main='outpvalue-outhlife', type='p', pch='+')

plot(density(data$inhlife), main='inhlife-distributioin')
plot(density(data$outhlife), main='outhlife-distributioin')

print(c(mean(data$outhlife), sd(data$outhlife)))

dev.off()

dbDisconnect(con)
dbUnloadDriver(drv)

