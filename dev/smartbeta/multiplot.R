library(xts)
library(zoo)
library(ggplot2)
library(reshape2)

multiplot <- function(price)
{
  price.df = as.data.frame(coredata(price))
  price.df$date = index(price)
  price.melt = melt(price.df, id='date', variable.name = "code", value.name='price')
  ggplot(data=price.melt, aes(x=date,y=price,group=code,col=code))+geom_line()
}

rebase <- function(xx, newbase=100)
{
  # rescale series to the same starting base.
  
  # xx is a matrix or data frame, rebase each series (as columns) to newbase
  
  # extend 0 in price series
  xx[which(xx==0)] = NA
  yy = na.fill(xx, 'extend')
  
  yy = sweep(yy, 2, yy[1,], `/`) * newbase
  return(yy)
}

data = read.zoo('citic.level1.csv', sep=',', header=T)
data = xts(data)
price = data[,seq(from=1,by=2,length.out=NCOL(data)/2)]

multiplot(rebase(price['2014-06-20/']))

