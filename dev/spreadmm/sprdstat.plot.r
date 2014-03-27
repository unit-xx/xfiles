statsfn = paste('sprdstats', tunit, qfn.base, 'pdf', sep='.')

pdf(statsfn, width=17.55, height=11.07)

plot(ccstats, pch='+', type='o', main=paste('cc stats for', qfn.base))
plot(dccstats, pch='+', type='o', main=paste('cc diff stats for', qfn.base))
plot(tsprdstats, pch='+', type='o', main=paste('tsprd stats for', qfn.base))
plot(rsprdstats, pch='+', type='o', main=paste('rsprd stats for', qfn.base))

dev.off()

