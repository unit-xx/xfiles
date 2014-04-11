# could order book imbalance be used to predict price movement?

qfn = '..\\spreadmm\\20140401.if1'
quote = read.table(qfn, header=T, colClasses=c('character','character','integer', 'character','numeric','numeric','numeric','numeric','numeric','numeric'))
# filter out non trading quotes
quote = quote[which(quote$buyvolume1>0 | quote$sellvolume1>0),]

qmid = (quote$buyprice1 + quote$sellprice1)/2
qlast = quote$lastprice
bidvoln = quote$buyvolume1 / mean(quote$buyvolume1)
askvoln = quote$sellvolume1 / mean(quote$sellvolume1)

H = 1
lag = 1
obratio = (bidvoln + H) / (bidvoln + askvoln + 2*H)
#obratio = (quote$buyvolume1) / (quote$buyvolume1 + quote$sellvolume1)
qdiff = diff(qmid, lag)

obratio = obratio[1:(length(obratio)-lag)]
plot(obratio, qdiff)
abline(h=0.0, v=0.5, col='red')

k = lm(qdiff~obratio)
summary(k)

range = 10000:10100
plot(range, obratio[range], type='s', main=mean(obratio[range]))
abline(h=mean(obratio[range]))

plot((bidvoln - askvoln)[range], type='s', main=mean((bidvoln - askvoln)[range]))

plot(range, qmid[range], type='s')

# NOTE: when obratio is large in a period, price may not go up as our first guess.
# but, it may be an indicator that the a trend is going to disembark.

maitvl = 50
obratio.ma = sapply(1:(length(obratio)-maitvl), 
                    function(i, seqx, len) {return(mean(seqx[i:(i+len-1)]))},
                    obratio,
                    maitvl
                    )
plot(obratio.ma, type='l')
plot(qmid, type='l')