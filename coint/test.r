
ema <- function (x, lambda = 0.1, startup = 0) 
{
    y = as.vector(x)
    if (lambda >= 1) 
        lambda = 2/(lambda + 1)
    if (startup == 0) 
        startup = floor(2/lambda)
    if (lambda == 0) {
        ema = rep(mean(x), length(x))
    }
    if (lambda > 0) {
        ylam = y * lambda
        ylam[1] = mean(y[1:startup])
        ema = filter(ylam, filter = (1 - lambda), method = "rec")
    }
    x = as.vector(ema)
    x
}

args <- commandArgs(TRUE)
print(args)
x=c(1,2,3,4,5)
pdf('test.pdf')
plot(x,x)
title('最最', family='song')
mtext('最最', family='song')
xxx=0
if (FALSE) xxx=1
print(xxx)
dev.off()
warnings()
