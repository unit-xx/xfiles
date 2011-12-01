t <- function(a, b=c('short','long','both'))
{
    print(a)
    print(match.arg(b))
}

if (1==1)
{
    print(1)
} else
{
    print(0)
}

t(1, 's')
