library(ggplot2)

args = commandArgs(T)

rptfn = 'alltrdrpt'

rptfn = args[1]
rptfnset = read.table(rptfn, header=F, stringsAsFactors=F)[,1]

allrpt.list = list()

for(i in 1:length(rptfnset))
{
  allrpt.list[[i]] = read.csv(rptfnset[i], header=T)
}

all.rpt = do.call(rbind, allrpt.list)

# total profit by maxprofit param
all.rpt.agg1 = aggregate(stoppnl~maxprofitparam, data=all.rpt, FUN=sum)
ggplot(all.rpt.agg1, aes(y=stoppnl, x=maxprofitparam)) + geom_line() + geom_point()

# average profit by maxprofit param
all.rpt.agg2 = aggregate(stoppnl~maxprofitparam, data=all.rpt, FUN=mean)
ggplot(all.rpt.agg2, aes(y=stoppnl, x=maxprofitparam)) + geom_line() + geom_point()

# win-loss ratio
all.rpt.agg3 = aggregate(stoppnl~maxprofitparam, data=all.rpt, FUN=function(x) {length(which(x>0))})
ggplot(all.rpt.agg3, aes(y=stoppnl, x=maxprofitparam)) + geom_line() + geom_point()

# by close type
ggplot(all.rpt, aes(x=factor(maxprofitparam), fill=factor(stopby))) + geom_bar(stat='bin')

# profit by maxprofit and close type
all.rpt.agg4 = aggregate(stoppnl~maxprofitparam+stopby, data=all.rpt, FUN=sum)
ggplot(all.rpt.agg4, aes(y=stoppnl, x=maxprofitparam, group=stopby, col=stopby)) + geom_line()

all.rpt.agg5 = aggregate(stoppnl~maxprofitparam+stopby, data=all.rpt, FUN=mean)
ggplot(all.rpt.agg5, aes(y=stoppnl, x=maxprofitparam, group=stopby, col=stopby)) + geom_line()

all.rpt.agg6 = aggregate(stoppnl~maxprofitparam+stopby, data=all.rpt, FUN=length)
ggplot(all.rpt.agg6, aes(y=stoppnl, x=maxprofitparam, group=stopby, col=stopby)) + geom_line()

ggplot(all.rpt, aes(x=factor(maxprofitparam), y=stoppnl, fill=factor(stopby), group=factor(stopby))) + geom_bar(stat='identity')

write.csv(all.rpt, 'xxx.csv', row.names=F)
