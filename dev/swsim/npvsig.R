library(ggplot2)
library(directlabels)

a = read.csv('npv3a.csv', header=T)
b = read.csv('npv3b.csv', header=T)
ab = rbind(a, b)

npvsig = aggregate(NPV~sig+B0, data=ab, FUN=mean)

plt = ggplot(data=npvsig, aes(x=B0, y=NPV, group=sig, col=sig)) + geom_smooth(se=F) + scale_color_continuous()
plt

a = ggplot(data=npvsig, aes(x=B0, y=sig, z=NPV)) + geom_smooth(se=F) + stat_contour(aes(colour = ..level..))

a = ggplot(data=npvsig, aes(x=B0, y=NPV, group=sig, col=sig)) + geom_line()

a = ggplot(data=npvsig, aes(x=B0, y=sig, z=NPV)) + stat_contour(aes(colour = ..level..))

direct.label(a)

a = ggplot(data=npvsig, aes(x=B0, y=NPV, z=sig)) + stat_contour(aes(colour = ..level..))