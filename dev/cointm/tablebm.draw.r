library(RSQLite)
library(lattice)

# take results from tablebm, and draw surface/contour plot.

tablebm.draw <- function(tag, left, right)
{
# wireframe(tearn~u*l, data=d, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),scales = list(arrows = FALSE))

    bmfn = paste(left, paste(right, collapse='.'), tag, 'tblbm', sep='.')
    d = read.table(bmfn, header=TRUE)

    # find range for u and l where tx count > 0
    urange = sort(unique(d$u))
    umin = 0
    umax = 0
    for (uu in urange)
    {
        txcnt = d$tcount[which(d$u==uu)]
        if (any(txcnt!=0)) {umin = uu; break}
    }
    urange = rev(urange)
    for (uu in urange)
    {
        txcnt = d$tcount[which(d$u==uu)]
        if (any(txcnt!=0)) {umax = uu; break}
    }

    lrange = sort(unique(d$l))
    lmin = 0
    lmax = 0
    for (ll in lrange)
    {
        txcnt = d$tcount[which(d$l==ll)]
        if (any(txcnt!=0)) {lmin = ll; break}
    }
    lrange = rev(lrange)
    for (ll in lrange)
    {
        txcnt = d$tcount[which(d$l==ll)]
        if (any(txcnt!=0)) {lmax = ll; break}
    }
    tmp = which(d$u>=umin)
    tmp = intersect(tmp, which(d$u<=umax))
    tmp = intersect(tmp, which(d$l>=lmin))
    tmp = intersect(tmp, which(d$l<=lmax))
    d = d[tmp,]

    pwidth = 17.55
    pheight = 8.3
    trellis.device(pdf, file=paste(bmfn, 'pdf', sep='.'), width=pwidth, height=pheight)
    nx = 4
    ny = 2
    unit = min(pwidth/nx/1.3, pheight/ny/1.1)

    gwidth = list(x=unit, unit='inches')
    gheight = list(x=unit, unit='inches')
    colorpal = terrain.colors(100, 1)

    #g <- wireframe(tearn~u*l, data=d, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),scales = list(arrows = FALSE), main='Total ABS Profit', colorkey=list(space='left'), col.regions=colorpal)
    #plot(g, split=c(1,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)
    #g <- contourplot(tearn~u*l, data=d, region=TRUE, cuts=15, scales = list(arrows = TRUE), colorkey=FALSE, col.regions=colorpal)
    #plot(g, split=c(1,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)

    #g <- wireframe(avgearn~u*l, data=d, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),scales = list(arrows = FALSE), main='Average ABS Profit', colorkey=list(space='left'), col.regions=colorpal)
    #plot(g, split=c(2,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)
    #g <- contourplot(avgearn~u*l, data=d, region=TRUE, cuts=15, scales = list(arrows = TRUE), colorkey=FALSE, col.regions=colorpal)
    #plot(g, split=c(2,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)

    #g <- wireframe(sdearn~u*l, data=d, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),scales = list(arrows = FALSE), main='ABS Profit stdev', colorkey=list(space='left'), col.regions=colorpal)
    #plot(g, split=c(3,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)
    #g <- contourplot(sdearn~u*l, data=d, region=TRUE, cuts=15, scales = list(arrows = TRUE), colorkey=FALSE, col.regions=colorpal)
    #plot(g, split=c(3,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)

    g <- wireframe(trelearn~u*l, data=d, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),scales = list(arrows = FALSE), main='Total REL Profit', colorkey=list(space='left'), col.regions=colorpal)
    plot(g, split=c(1,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)
    g <- contourplot(trelearn~u*l, data=d, region=TRUE, cuts=15, scales = list(arrows = TRUE), colorkey=FALSE, col.regions=colorpal)
    plot(g, split=c(1,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)

    g <- wireframe(sharpeyear~u*l, data=d, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),scales = list(arrows = FALSE), main='Sharpe Ratio', colorkey=list(space='left'), col.regions=colorpal)
    plot(g, split=c(2,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)
    g <- contourplot(sharpeyear~u*l, data=d, region=TRUE, cuts=15, scales = list(arrows = TRUE), colorkey=FALSE, col.regions=colorpal)
    plot(g, split=c(2,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=T)

    #g <- wireframe(sdcost~u*l, data=d, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),scales = list(arrows = FALSE), main='Tx cost stdev', colorkey=list(space='left'), col.regions=colorpal)
    #plot(g, split=c(2,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)
    #g <- contourplot(sdcost~u*l, data=d, region=TRUE, cuts=15, scales = list(arrows = TRUE), colorkey=FALSE, col.regions=colorpal)
    #plot(g, split=c(2,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)

    g <- wireframe(avgtxdur~u*l, data=d, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),scales = list(arrows = FALSE), main='Average Tx duration', colorkey=list(space='left'), col.regions=colorpal)
    plot(g, split=c(3,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)
    g <- contourplot(avgtxdur~u*l, data=d, region=TRUE, cuts=15, scales = list(arrows = TRUE), colorkey=FALSE, col.regions=colorpal)
    plot(g, split=c(3,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)

    g <- wireframe(maxdd~u*l, data=d, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),scales = list(arrows = FALSE), main='Max drawdown', colorkey=list(space='left'), col.regions=colorpal)
    plot(g, split=c(4,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)
    g <- contourplot(maxdd~u*l, data=d, region=TRUE, cuts=15, scales = list(arrows = FALSE), colorkey=FALSE, col.regions=colorpal)
    plot(g, split=c(4,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=F)

    # start new page
    g <- wireframe(tcount~u*l, data=d, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),scales = list(arrows = FALSE), main='Tx count', colorkey=list(space='left'), col.regions=colorpal)
    plot(g, split=c(1,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)
    g <- contourplot(tcount~u*l, data=d, region=TRUE, cuts=15, scales = list(arrows = FALSE), colorkey=FALSE, col.regions=colorpal)
    plot(g, split=c(1,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=T)

    g <- wireframe(avgrelearn~u*l, data=d, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),scales = list(arrows = FALSE), main='Average REL Profit', colorkey=list(space='left'), col.regions=colorpal)
    plot(g, split=c(2,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)
    g <- contourplot(avgrelearn~u*l, data=d, region=TRUE, cuts=15, scales = list(arrows = TRUE), colorkey=FALSE, col.regions=colorpal)
    plot(g, split=c(2,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)

    g <- wireframe(sdrelearn~u*l, data=d, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),scales = list(arrows = FALSE), main='REL Profit stdev', colorkey=list(space='left'), col.regions=colorpal)
    plot(g, split=c(3,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)
    g <- contourplot(sdrelearn~u*l, data=d, region=TRUE, cuts=15, scales = list(arrows = TRUE), colorkey=FALSE, col.regions=colorpal)
    plot(g, split=c(3,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)

    g <- wireframe(avgcost~u*l, data=d, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),scales = list(arrows = FALSE), main='Average Tx cost', colorkey=list(space='left'), col.regions=colorpal)
    plot(g, split=c(4,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)
    g <- contourplot(avgcost~u*l, data=d, region=TRUE, cuts=15, scales = list(arrows = TRUE), colorkey=FALSE, col.regions=colorpal)
    plot(g, split=c(4,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=F)

    par(mfrow=c(2,2))
    plot(trelearn~sharpeyear, data=d, main='total rel earn vs. sharpe ratio')
    plot(maxdd~sharpeyear, data=d, main='max drawdown vs. sharpe, ratio')
    plot(avgtxdur~sharpeyear, data=d, main='avg tx duration vs. sharpe ratio')
    plot(tcount~sharpeyear, data=d, main='total tx count vs. sharpe ratio')

    dev.off()
}

args <- commandArgs(TRUE)
if (length(args) < 1) stop("tablebm.draw.r visualplan")

print(args)
plan <- read.table(args[1], row.names=1, sep='=', colClasses='character', strip.white=TRUE)

tag = plan['tag', 1]
startdate = as.Date(plan['visualfrom', 1])
enddate = as.Date(plan['visualto', 1])

drv = dbDriver('SQLite')
con <- dbConnect(drv, dbname = plan['cointdb', 1])

tovisual <- dbGetQuery(con, plan['visuallist', 1])
if (!is.na(plan['visualfile', 1]))
{
    visualfile <- read.table(plan['visualfile', 1], col.names='cpair', stringsAsFactors=F, colClasses='character', strip.white=TRUE)
    tovisual <- as.data.frame(union(tovisual, visualfile))
    names(tovisual) = 'cpair'
}

setwd(plan['dbdir', 1])
for (i in 1:nrow(tovisual))
{
    cpair <- tovisual[i,]

    tmp <- unlist(strsplit(cpair, "\\."))
    left <- tmp[1]
    right <- tmp[2:length(tmp)]
    print(c(i, cpair))

    tablebm.draw(tag, left, right)
}
setwd('..')
