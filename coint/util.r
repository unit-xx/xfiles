ema <- function (x, lambda = 0.1, startup = 0, startup.as=0)
{
    # startup.as == 0 : calculate startup value from x
    # startup.as == 1 : use startup as startup value
    y = as.vector(x)
    if (lambda >= 1)
        lambda = 2/(lambda + 1)
    if (startup == 0)
        startup = floor(2/lambda/2.8854)
    if (lambda == 0) {
        ema = rep(mean(x), length(x))
    }
    if (lambda > 0) {
        ylam = y * lambda
        if (startup.as == 0)
        {
            ylam[1] = mean(y[1:startup])
        }
        else
        {
            ylam[1] = startup*(1-lambda) + ylam[1]*lambda
        }
        ema = filter(ylam, filter = (1 - lambda), method = "rec")
    }
    x = as.vector(ema)
    x
}

ouhlife <- function(spread)
{
    s = as.vector(spread)
    sp = s[2:length(s)]
    s = s[1:length(s)-1]
    ds = sp - s
    smean = mean(spread)
    s = s - smean
    rst = lm (ds ~ s + 0)
    hlife = -log(2)/coef(rst)[1];
    hlife
}
