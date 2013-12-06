a = read.csv('sample.csv')
plot(a$EDsum, type='l', main='EDsum')
plot(a$NPV, type='l', main='NPV')

plot(density(a$EDsum))
plot(density(a$NPV))

hist(a$EDsum)
hist(a$NPV)

summary(a$NPV)
sd(a$NPV)