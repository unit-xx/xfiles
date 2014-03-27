# read perf and visualize performance using 3-D & contour graph

library(lattice)

qfn.base = '201305'
args = commandArgs(T)
if(length(args) > 0) qfn.base=args[1]

dorev = F
if(length(args) > 1) dorev = (as.numeric(args[2])==-1)
if (dorev)
{
  daytag = 'rev'
} else
{
  daytag = 'norm'
}

pwidth = 17.55
pheight = 8.3
nx = 3
ny = 2
unit = min(pwidth/nx/1.3, pheight/ny/1.2)
gwidth = list(x=unit, unit='inches')
gheight = list(x=unit, unit='inches')
colorpal = terrain.colors(100,1)

# for each day
perffn = paste('mmzjperf', daytag, qfn.base, 'csv', sep='.')
tperf = read.csv(perffn, stringsAsFactors=F)

days = unique(tperf$day)

doplot <- function(dperf, colorpal, day, nx, ny, gwidth, gheight)
{
  #ntrd
  g = wireframe(ntrd~stopprofit*stoploss, data=dperf, light.source=c(2,1,10), drape=T, aspect=c(1,1),
                screen=list(z=-40,x=-60,y=0), scales=list(arrows=F),
                main=paste('ntrd', format(day), sep=' '), colorkey=list(space='left'), col.regions=colorpal)
  plot(g, split=c(1,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=T)
  
  g = contourplot(ntrd~stopprofit*stoploss, data=dperf, region=T, couts=10, scales=list(arrows=T),
                  colorkey=F, col.regions=colorpal)
  plot(g, split=c(1,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=T)
  
  #prft without tx
  g = wireframe(prft~stopprofit*stoploss, data=dperf, light.source=c(2,1,10), drape=T, aspect=c(1,1),
                screen=list(z=-40,x=-60,y=0), scales=list(arrows=F),
                main='prft w/o tx', colorkey=list(space='left'), col.regions=colorpal)
  plot(g, split=c(2,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=T)
  
  g = contourplot(prft~stopprofit*stoploss, data=dperf, region=T, couts=10, scales=list(arrows=T),
                  colorkey=F, col.regions=colorpal)
  plot(g, split=c(2,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=T)

  #prft with tx
  g = wireframe(prfttx~stopprofit*stoploss, data=dperf, light.source=c(2,1,10), drape=T, aspect=c(1,1),
                screen=list(z=-40,x=-60,y=0), scales=list(arrows=F),
                main='prft with tx', colorkey=list(space='left'), col.regions=colorpal)
  plot(g, split=c(3,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=T)
  
  g = contourplot(prfttx~stopprofit*stoploss, data=dperf, region=T, couts=10, scales=list(arrows=T),
                  colorkey=F, col.regions=colorpal)
  plot(g, split=c(3,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=F)
  
}

trellis.device(pdf, file=paste('mmzjperf', daytag, qfn.base, 'pdf', sep='.'), 
               width=pwidth, height=pheight)

for(i in 1:length(days))
{
  # do graphing
  d = days[i]
  idx = which(tperf$day == d)
  # daily spread
  dperf = tperf[idx,]
  
  doplot(dperf, colorpal, d, nx, ny, gwidth, gheight)
}

aggby = c('stopprofit', 'stoploss')

tperf.avg = aggregate(tperf[,-1], by=tperf[,aggby], function(x){mean(x, na.rm=T)})
doplot(tperf.avg, colorpal, 'all day average', nx, ny, gwidth, gheight)

tperf.sd = aggregate(tperf[,-1], by=tperf[,aggby], function(x){sd(x, na.rm=T)})
doplot(tperf.sd, colorpal, 'all day sd', nx, ny, gwidth, gheight)

tperf.mad = aggregate(tperf[,-1], by=tperf[,aggby], function(x){mad(x, na.rm=T)})
doplot(tperf.mad, colorpal, 'all day mad', nx, ny, gwidth, gheight)

dev.off()