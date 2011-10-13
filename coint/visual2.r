library(zoo)

args <- commandArgs(TRUE)

setwd('data')

s1 <- read.csv(args[1], stringsAsFactors=F)
s1_date <- as.Date(as.character(s1$DATE), '%Y%m%d')

s2 <- read.csv(args[2], stringsAsFactors=F)
s2_date <- as.Date(as.character(s1$DATE), '%Y%m%d')

beta = 0.857560096865843

s1 <- zoo(s1$PRECLOSE, s1_date)
s2 <- zoo(s2$PRECLOSE, s2_date)

s.zoo <- merge(s1, s2, all=FALSE)
s <- as.data.frame(s.zoo)

cat("Date range is", format(start(s.zoo)), "to", format(end(s.zoo)), "\n")

sprd <- s$s1 - beta*s$s2
print(mean(sprd))
print(sd(sprd))

setwd('..')
pdf('visual.pdf', width=11.7, height=8.3)
plot(s.zoo$s1-beta*s.zoo$s2)
#lines(s.zoo$s1, col='blue')
#lines(s.zoo$s2, col='red')
dev.off()
