args = commandArgs(T)

pp = read.table(args[1], fill=T, stringsAsFactors=F)

pdf(args[2], width=17.55, height=11.07)
for(i in 1:NROW(pp))
{
  if(pp[i,1]=='beginframe')
  {
    beginid = i
  }

  if(pp[i,1]=='endframe')
  {
    endid = i
    toplot = pp[(beginid+1):(endid-1),c(3,4,5,6)]
    
    plot(toplot[,1], toplot[,2], pch=toplot[,3], col=toplot[,4], type='n')
    abline(v=seq(0, max(toplot[,1]), 1), col="lightgray", lty="dotted")
    abline(h=seq(min(toplot[,2]), max(toplot[,2]), 0.2), col="lightgray", lty="dotted")
    points(toplot[,1], toplot[,2], pch=toplot[,3], col=toplot[,4])
  }
}
dev.off()

# $Id$


