# read perf and visualize performance using 3-D & contour graph

# TODO: plot quotes after plot.

library(lattice)

qfn.base = '201301'
args = commandArgs(T)
if(length(args) > 0) qfn.base=args[1]

qmax = 1
if(length(args) > 1) qmax=as.integer(args[2])

wsize = 120
if(length(args) > 1) wsize = as.integer(args[3])

pwidth = 17.55
pheight = 8.3
nx = 4
ny = 2
unit = min(pwidth/nx/1.3, pheight/ny/1.1)
gwidth = list(x=unit, unit='inches')
gheight = list(x=unit, unit='inches')
colorpal = terrain.colors(100,1)

# for each day
perffn = paste('mmiterbtperf', qfn.base, paste('q',qmax,sep=''), paste('w',wsize,sep=''), 'csv', sep='.')
tperf = read.csv(perffn)

#filter out sigadj=0.0 records
o = which(tperf$sigadj!=0.0)
tperf = tperf[o,]

days = unique(tperf$tidx)

doplot <- function(dperf, colorpal, day, nx, ny, gwidth, gheight)
{
  #ntrd
  g = wireframe(ntrd~tintns*sigadj, data=dperf, light.source=c(2,1,10), drape=T, aspect=c(1,1),
                screen=list(z=-40,x=-60,y=0), scales=list(arrows=F),
                main=paste('ntrd', format(day), sep=' '), colorkey=list(space='left'), col.regions=colorpal)
  plot(g, split=c(1,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=T)
  
  g = contourplot(ntrd~tintns*sigadj, data=dperf, region=T, couts=10, scales=list(arrows=T),
                  colorkey=F, col.regions=colorpal)
  plot(g, split=c(1,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=T)
  
  
  #nshort
  g = wireframe(nshort~tintns*sigadj, data=dperf, light.source=c(2,1,10), drape=T, aspect=c(1,1),
                screen=list(z=-40,x=-60,y=0), scales=list(arrows=F),
                main='nshort', colorkey=list(space='left'), col.regions=colorpal)
  plot(g, split=c(2,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=T)
  
  g = contourplot(nshort~tintns*sigadj, data=dperf, region=T, couts=10, scales=list(arrows=T),
                  colorkey=F, col.regions=colorpal)
  plot(g, split=c(2,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=T)
  
  
  #nlong
  g = wireframe(nlong~tintns*sigadj, data=dperf, light.source=c(2,1,10), drape=T, aspect=c(1,1),
                screen=list(z=-40,x=-60,y=0), scales=list(arrows=F),
                main='nlong', colorkey=list(space='left'), col.regions=colorpal)
  plot(g, split=c(3,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=T)
  
  g = contourplot(nlong~tintns*sigadj, data=dperf, region=T, couts=10, scales=list(arrows=T),
                  colorkey=F, col.regions=colorpal)
  plot(g, split=c(3,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=T)
  
  
  #nmismatch
  g = wireframe(nmismatch~tintns*sigadj, data=dperf, light.source=c(2,1,10), drape=T, aspect=c(1,1),
                screen=list(z=-40,x=-60,y=0), scales=list(arrows=F),
                main='nmismatch', colorkey=list(space='left'), col.regions=colorpal)
  plot(g, split=c(4,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=T)
  
  g = contourplot(nmismatch~tintns*sigadj, data=dperf, region=T, couts=10, scales=list(arrows=T),
                  colorkey=F, col.regions=colorpal)
  plot(g, split=c(4,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=F)
  
  
  #prft
  g = wireframe(prft~tintns*sigadj, data=dperf, light.source=c(2,1,10), drape=T, aspect=c(1,1),
                screen=list(z=-40,x=-60,y=0), scales=list(arrows=F),
                main='prft', colorkey=list(space='left'), col.regions=colorpal)
  plot(g, split=c(1,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=T)
  
  g = contourplot(prft~tintns*sigadj, data=dperf, region=T, couts=10, scales=list(arrows=T),
                  colorkey=F, col.regions=colorpal)
  plot(g, split=c(1,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=T)
  
  
  #implcost
  g = wireframe(implcost~tintns*sigadj, data=dperf, light.source=c(2,1,10), drape=T, aspect=c(1,1),
                screen=list(z=-40,x=-60,y=0), scales=list(arrows=F),
                main='implcost', colorkey=list(space='left'), col.regions=colorpal)
  plot(g, split=c(2,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=T)
  
  g = contourplot(implcost~tintns*sigadj, data=dperf, region=T, couts=10, scales=list(arrows=T),
                  colorkey=F, col.regions=colorpal)
  plot(g, split=c(2,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=F)
}

trellis.device(pdf, file=paste('mmiterbt.visual', qfn.base, paste('q',qmax,sep=''), paste('w',wsize,sep=''), 'pdf', sep='.'), width=pwidth, height=pheight)
for(i in 1:length(days))
{
  # do graphing
  d = days[i]
  idx = which(tperf$tidx == d)
  # daily spread
  dperf = tperf[idx,]
  
  doplot(dperf, colorpal, d, nx, ny, gwidth, gheight)
}
tperf.avg = aggregate(tperf[,-1], by=tperf[,c('tintns', 'sigadj')], function(x){mean(x, na.rm=T)})
doplot(tperf.avg, colorpal, 'all day average', nx, ny, gwidth, gheight)

tperf.sd = aggregate(tperf[,-1], by=tperf[,c('tintns', 'sigadj')], function(x){sd(x, na.rm=T)})
doplot(tperf.sd, colorpal, 'all day sd', nx, ny, gwidth, gheight)

tperf.mad = aggregate(tperf[,-1], by=tperf[,c('tintns', 'sigadj')], function(x){mad(x, na.rm=T)})
doplot(tperf.mad, colorpal, 'all day mad', nx, ny, gwidth, gheight)

dev.off()