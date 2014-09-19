args = commandArgs(T)

pp = read.table(args[1], fill=T, stringsAsFactors=F)

pdf(args[2], width=17.55*1.1, height=11.07)
for(i in 1:NROW(pp))
{
  if(pp[i,1]=='beginframe')
  {
    beginid = i
  }

  if(pp[i,1]=='endframe')
  {
    endid = i


    frame = pp[(beginid+1):(endid-1),]
    plottype = frame[,2]
    tag = frame[,1]

    points = which(plottype=='points')
    texts = which(plottype=='text')
    ts = which(plottype=='time')
    quotes = which(plottype=='points' & tag=='quote')

    toplot = frame[points,c(3,4,5,6)]
    totext = frame[texts,c(3,4,5,6)]
    timestamps = frame[ts, 5]
    quoteline = frame[quotes, c(3,4,5,6)]

    # replace string \\n with \n
    for(k in 1:NROW(totext))
    {
      totext[k,3] = gsub('\\n', '\n', totext[k,3], fixed=T)
    }

    topY = max(toplot[,2])
    

    plot(toplot[,1], toplot[,2], pch=toplot[,3], col=toplot[,4], type='n', xlab=sprintf('%s - %s', timestamps[1], timestamps[length(timestamps)]))

    # ask/bid lines
    askq = seq(1, length.out=length(quotes)/2, by=2)
    bidq = seq(2, length.out=length(quotes)/2, by=2)
    lines(quoteline[askq,1], quoteline[askq,2], col='brown1', lty='dashed', lwd=2)
    lines(quoteline[bidq,1], quoteline[bidq,2], col='brown1', lty='dashed', lwd=2)

    # grids
    abline(v=seq(0, max(toplot[,1]), 1), col="lightgray", lty="dotted")
    abline(h=seq(min(toplot[,2]), max(toplot[,2]), 0.2), col="lightgray", lty="dotted")
    abline(v=integer((endid-beginid)/2), col='lightgray', lty='solid')

    # quotes and limit orders
    text(toplot[,1], toplot[,2], labels=toplot[,3], col=toplot[,4])


    # text notes
    par(xpd=TRUE)
    text(totext[,1], topY, labels=totext[,3], col=totext[,4], pos=3, cex=2)
  }
}
dev.off()

# $Id$


