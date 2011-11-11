library(RSQLite)
library(lattice)

# take results from tablebm, and draw surface/contour plot.

tablebm.draw <- function(tag, left, right)
{
# wireframe(tearn~u*l, data=d, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),scales = list(arrows = FALSE))

    bmfn = paste(left, right, tag, 'tblbm', sep='.')
    d = read.table(bmfn, header=TRUE)

    pwidth = 17.55
    pheight = 8.3
    trellis.device(pdf, file=paste(bmfn, 'pdf', sep='.'), width=pwidth, height=pheight)
    nx = 4
    ny = 2
    unit = min(pwidth/nx/1.3, pheight/ny/1.1)

    gwidth = list(x=unit, unit='inches')
    gheight = list(x=unit, unit='inches')
    colorpal = terrain.colors(100, 1)

    g <- wireframe(tearn~u*l, data=d, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),scales = list(arrows = FALSE), main='Total Profit', colorkey=list(space='left'), col.regions=colorpal)
    plot(g, split=c(1,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)
    g <- contourplot(tearn~u*l, data=d, region=TRUE, cuts=15, scales = list(arrows = TRUE), colorkey=FALSE, col.regions=colorpal)
    plot(g, split=c(1,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)

    g <- wireframe(avgearn~u*l, data=d, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),scales = list(arrows = FALSE), main='Average Profit', colorkey=list(space='left'), col.regions=colorpal)
    plot(g, split=c(2,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)
    g <- contourplot(avgearn~u*l, data=d, region=TRUE, cuts=15, scales = list(arrows = TRUE), colorkey=FALSE, col.regions=colorpal)
    plot(g, split=c(2,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)

    g <- wireframe(sdearn~u*l, data=d, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),scales = list(arrows = FALSE), main='Profit stdev', colorkey=list(space='left'), col.regions=colorpal)
    plot(g, split=c(3,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)
    g <- contourplot(sdearn~u*l, data=d, region=TRUE, cuts=15, scales = list(arrows = TRUE), colorkey=FALSE, col.regions=colorpal)
    plot(g, split=c(3,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)

    g <- wireframe(tcount~u*l, data=d, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),scales = list(arrows = FALSE), main='Tx count', colorkey=list(space='left'), col.regions=colorpal)
    plot(g, split=c(4,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)
    g <- contourplot(tcount~u*l, data=d, region=TRUE, cuts=15, scales = list(arrows = FALSE), colorkey=FALSE, col.regions=colorpal)
    plot(g, split=c(4,2,nx,ny), panel.width=gwidth, panel.height=gheight)


    # start page 2
    g <- wireframe(avgcost~u*l, data=d, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),scales = list(arrows = FALSE), main='Average Tx cost', colorkey=list(space='left'), col.regions=colorpal)
    plot(g, split=c(1,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)
    g <- contourplot(avgcost~u*l, data=d, region=TRUE, cuts=15, scales = list(arrows = TRUE), colorkey=FALSE, col.regions=colorpal)
    plot(g, split=c(1,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)

    g <- wireframe(sdcost~u*l, data=d, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),scales = list(arrows = FALSE), main='Tx cost stdev', colorkey=list(space='left'), col.regions=colorpal)
    plot(g, split=c(2,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)
    g <- contourplot(sdcost~u*l, data=d, region=TRUE, cuts=15, scales = list(arrows = TRUE), colorkey=FALSE, col.regions=colorpal)
    plot(g, split=c(2,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)

    g <- wireframe(avgtxdur~u*l, data=d, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),scales = list(arrows = FALSE), main='Average Tx duration', colorkey=list(space='left'), col.regions=colorpal)
    plot(g, split=c(3,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)
    g <- contourplot(avgtxdur~u*l, data=d, region=TRUE, cuts=15, scales = list(arrows = TRUE), colorkey=FALSE, col.regions=colorpal)
    plot(g, split=c(3,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)

    g <- wireframe(sdtxdur~u*l, data=d, light.source = c(2,1,10), drape=TRUE, aspect = c(1,1),screen = list(z = -40, x = -60, y = 0),scales = list(arrows = FALSE), main='Tx duration stdev', colorkey=list(space='left'), col.regions=colorpal)
    plot(g, split=c(4,1,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)
    g <- contourplot(sdtxdur~u*l, data=d, region=TRUE, cuts=15, scales = list(arrows = FALSE), colorkey=FALSE, col.regions=colorpal)
    plot(g, split=c(4,2,nx,ny), panel.width=gwidth, panel.height=gheight, more=TRUE)
    dev.off()
}

args <- commandArgs(TRUE)
if (length(args) < 1) stop("tablebm.draw.r visualplan")

print(args)
plan <- read.table(args[1], row.names=1, sep='=', colClasses='character', strip.white=TRUE)

tag = plan['tag', 1]

drv = dbDriver('SQLite')
con <- dbConnect(drv, dbname = plan['cointdb', 1])
tovisual <- dbGetQuery(con, plan['visuallist', 1])
betafrom <- plan['betafrom', 1]
pttest <- dbReadTable(con, betafrom)
dbDisconnect(con)

tovisual <- merge(tovisual, pttest, by='cpair', all=FALSE)

setwd(plan['dbdir', 1])
for (i in 1:nrow(tovisual))
{
    cpair <- tovisual[i,]$cpair
    npair <- tovisual[i,]$npair
    beta <- as.numeric(tovisual[i,]$beta)

    tmp <- unlist(strsplit(cpair, "\\."))
    left <- tmp[1]
    right <- tmp[2]
    print(c(left, right))

    tablebm.draw(tag, left, right)
}
setwd('..')


