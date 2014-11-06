library(ggplot2)

args = commandArgs(T)

rptfn = 'alltrdrpt'

rptfn = args[1]
rptfnset = read.table(rptfn, header=F, stringsAsFactors=F)[,1]

allrpt.list = list()

for(i in 1:length(rptfnset))
{
  allrpt.list[[i]] = read.csv(rptfnset[i], header=T)
  print(i)
}

all.rpt = do.call(rbind, allrpt.list)

pdf('p1.pdf', width=17.55, height=11.07)
# NOTE: assume "maxlossparam","maxddparam" are fixed.
# TODO: add title, 

# total profit by maxprofit param
all.rpt.agg1 = aggregate(stoppnl~maxprofitparam, data=all.rpt, FUN=sum)
ggplot(all.rpt.agg1, aes(y=stoppnl, x=maxprofitparam)) + geom_line() + geom_point() + ggtitle('total profit')

# average profit by maxprofit param
all.rpt.agg2 = aggregate(stoppnl~maxprofitparam, data=all.rpt, FUN=mean)
ggplot(all.rpt.agg2, aes(y=stoppnl, x=maxprofitparam)) + geom_line() + geom_point() + ggtitle('average profit')

# win-loss ratio
all.rpt.agg3 = aggregate(stoppnl~maxprofitparam, data=all.rpt, FUN=function(x) {length(which(x>0))/length(x)})
ggplot(all.rpt.agg3, aes(y=stoppnl, x=maxprofitparam)) + geom_line() + geom_point() + ggtitle('win-loss count ratio')

# win-loss points ratio
all.rpt.agg4 = aggregate(stoppnl~maxprofitparam, data=all.rpt, FUN=function(x) {-sum(x[which(x>0)])/sum(x[which(x<0)])})
ggplot(all.rpt.agg4, aes(y=stoppnl, x=maxprofitparam)) + geom_line() + geom_point() + ggtitle('win-loss points ratio')

# win points
all.rpt.agg5 = aggregate(stoppnl~maxprofitparam, data=all.rpt, FUN=function(x) {sum(x[which(x>0)])})
ggplot(all.rpt.agg5, aes(y=stoppnl, x=maxprofitparam)) + geom_line() + geom_point() + ggtitle('total win points')

# loss points
all.rpt.agg6 = aggregate(stoppnl~maxprofitparam, data=all.rpt, FUN=function(x) {-sum(x[which(x<0)])})
ggplot(all.rpt.agg6, aes(y=stoppnl, x=maxprofitparam)) + geom_line() + geom_point() + ggtitle('total loss points')

# slice of pnl on specified maxprofitparam
for(i in sort(unique(all.rpt$maxprofitparam)))
{
  slice = all.rpt$stoppnl[which(all.rpt$maxprofitparam==i)]
  slice.xts = xts(slice, order.by=as.Date(all.rpt$date[which(all.rpt$maxprofitparam==i)]))
  barplot(slice.xts, main=sprintf('pnl when maxprofit=%d', i))
  cumslice = cumsum(slice)
  plot(cumslice, type='o')
}

dev.off()

# by close type
# ggplot(all.rpt, aes(x=factor(maxprofitparam), fill=factor(stopby))) + geom_bar(stat='bin')

# profit by maxprofit and close type
# all.rpt.agg4 = aggregate(stoppnl~maxprofitparam+stopby, data=all.rpt, FUN=sum)
# ggplot(all.rpt.agg4, aes(y=stoppnl, x=maxprofitparam, group=stopby, col=stopby)) + geom_line()
# 
# all.rpt.agg5 = aggregate(stoppnl~maxprofitparam+stopby, data=all.rpt, FUN=mean)
# ggplot(all.rpt.agg5, aes(y=stoppnl, x=maxprofitparam, group=stopby, col=stopby)) + geom_line()
# 
# all.rpt.agg6 = aggregate(stoppnl~maxprofitparam+stopby, data=all.rpt, FUN=length)
# ggplot(all.rpt.agg6, aes(y=stoppnl, x=maxprofitparam, group=stopby, col=stopby)) + geom_line()
# 
# ggplot(all.rpt, aes(x=factor(maxprofitparam), y=stoppnl, fill=factor(stopby), group=factor(stopby))) + geom_bar(stat='identity')
# 
# write.csv(all.rpt, 'xxx.csv', row.names=F)
