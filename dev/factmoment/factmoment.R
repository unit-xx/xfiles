# calculate factorial moment in rolling windows, draw the result along with price

# params:
# quote file:
# code: IFxxxx
# tick per bin: how many ticks in a bin
# bin per window: how many bin in a window
# step: bin differences between consequtive windows.
# q: q in factorial moment formulae
# type: moment type, +/-/+-

qfn = '..\\spreadmm\\20140310.if1'
tpb = 20
bpw = 20
step = 1
q = 2
type = '+'

quote = read.table(qfn, header=T, colClasses=c('character','character','integer', 'character','numeric','numeric','numeric','numeric'))
# filter out non trading quotes
quote = quote[which(quote$buyvolume1>0 | quote$sellvolume1>0),]

qmid = (quote$buyprice1+quote$sellprice1)/2
qdiff = diff(qmid)

# step 1: count +/- in each bin

seqdo <- function(i, seqx, len, type)
{
  s = seqx[i:(i+len-1)]
  if (type=='+')
  {
    n = length(which(s>0))
  }
  else if (type=='-')
  {
    n = length(which(s<0))
  }
  else
  {
    n = -1
  }
  return(n)
}

fmcalc <- function(i, seqx, len, q)
{
  s = seqx[i:(i+len-1)]
  s1 = sapply(s, function(x,q) {prod(seq(x,by=-1,length.out=q))}, q)
  ret = mean(s1) / mean(s)**q
  return(ret)
}

startind = seq(1, by=tpb, length.out=as.integer(length(qdiff)/tpb))

binrst1 = sapply(startind, seqdo, qdiff, tpb, '+')
fm1 = sapply(seq(1, length(binrst1)-bpw+1), fmcalc, binrst1, bpw, q)

binrst2 = sapply(startind, seqdo, qdiff, tpb, '-')
fm2 = sapply(seq(1, length(binrst1)-bpw+1), fmcalc, binrst2, bpw, q)
