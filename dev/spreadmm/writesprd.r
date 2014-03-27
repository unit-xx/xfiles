library(zoo)
library(chron)

source('util.r')

qfn.base = '20140214'

args = commandArgs(T)
if(length(args) > 0) qfn.base=args[1]

options(digits.secs=3) # for milliseconds parsing and display

if1.suf = 'if1'
if2.suf = 'if2'

print(sprintf('Processing ... %s', qfn.base))

qfn1 = paste(qfn.base, if1.suf, sep='.')
qfn2 = paste(qfn.base, if2.suf, sep='.')

print('Reading Quotations')
q1.zoo = read.quote(qfn1)
q2.zoo = read.quote(qfn2)

# merge by 'outer join'
qa = merge(q1.zoo, q2.zoo, all=T, suffixes=c('q1', 'q2'))
# fill gap with latest updates
qa2 = na.locf(qa, na.rm=T) # fill gap with last quotation update

print('Calc Spreads')
bidsprd = qa2$buyprice1.q2 - qa2$sellprice1.q1
asksprd = qa2$sellprice1.q2 - qa2$buyprice1.q1
midsprd = (bidsprd+asksprd)/2
badiff = asksprd-bidsprd
sprd = cbind(bidsprd, asksprd, midsprd, badiff)
# remove the NAs in the first line for the extreme case
sprd = na.locf(sprd, na.rm=T)

print('Write Spreads')
sprdfn = paste('sprd', qfn.base, 'csv', sep='.')
write.sprd(sprdfn, sprd)
