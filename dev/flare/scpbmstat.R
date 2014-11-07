library(ggplot2)

args = commandArgs(T)

rptfn = 'allbmrpt'

rptfn = args[1]
rptfnset = read.table(rptfn, header=F, stringsAsFactors=F)[,1]

allrpt.list = list()

for(i in 1:length(rptfnset))
{
  allrpt.list[[i]] = read.csv(rptfnset[i], header=T)
  print(i)
}

all.rpt = do.call(rbind, allrpt.list)

nday = length(allrpt.list)
trdstat = data.frame(
  winlosscntratio = numeric(nday),
  winlosspntratio = numeric(nday),
  date = character(nday),
  stringsAsFactors=F
)

# stat for each day
for(i in 1:length(allrpt.list))
{
  dayrpt = allrpt.list[[i]]
  wins = length(which(dayrpt$stoppnl>0))
  loss = length(which(dayrpt$stoppnl<0))
  winpt = sum(dayrpt$stoppnl[which(dayrpt$stoppnl>0)])
  losspt = -sum(dayrpt$stoppnl[which(dayrpt$stoppnl<0)])
  trdstat$winlosscntratio[i] = wins/loss
  trdstat$winlosspntratio[i] = winpt/losspt
  trdstat$date[i] = as.character(dayrpt$date[1])
}

wins = length(which(all.rpt$stoppnl>0))
loss = length(which(all.rpt$stoppnl<0))
winpt = sum(all.rpt$stoppnl[which(all.rpt$stoppnl>0)])
losspt = -sum(all.rpt$stoppnl[which(all.rpt$stoppnl<0)])
allwinlosscntratio = wins/loss
allwinlosspntratio = winpt/losspt

pdf('bmstat.pdf', width=17.55, height=11.07)

plot(1:10, type='n', main=sprintf('total winloss count ratio=%.3f, winloss point ratio=%.3f', allwinlosscntratio, allwinlosspntratio))
plot(xts(trdstat$winlosscntratio, order.by=as.Date(trdstat$date)), type='o', main='total win-loss count ratio')
plot(xts(trdstat$winlosspntratio, order.by=as.Date(trdstat$date)), type='o', main='total win-loss point ratio')

dev.off()

