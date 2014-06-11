args = commandArgs(T)

pp = read.table(args[1], fill=T, stringsAsFactors=F)

pdf('xxx.pdf')
for(i in 1:NROW(pp))
{
  if(pp[i,1]=='beginframe')
  {
    beginid = i
  }

  if(pp[i,1]=='endframe')
  {
    endid = i
    toplot = pp[(beginid+1):(endid+1),c(3,4)]

    plot(toplot)
  }
}
dev.off()

# $Id$


