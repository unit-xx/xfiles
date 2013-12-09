library(ggplot2)
library(directlabels)

ab = read.csv('s0sig.csv', header=T)

valuesig = aggregate(value~sig+s0, data=ab, FUN=mean)

plt = ggplot(data=valuesig, aes(x=s0, y=value, group=sig, col=sig)) + geom_smooth(se=F) + scale_color_continuous()
plt

a = ggplot(data=valuesig, aes(x=s0, y=sig, z=value)) + geom_smooth(se=F) + stat_contour(aes(colour = ..level..))

a = ggplot(data=valuesig, aes(x=s0, y=value, group=sig, col=sig)) + geom_line()

a = ggplot(data=valuesig, aes(x=s0, y=sig, z=value)) + stat_contour(aes(colour = ..level..))

direct.label(a)

a = ggplot(data=valuesig, aes(x=s0, y=value, z=sig)) + stat_contour(aes(colour = ..level..))