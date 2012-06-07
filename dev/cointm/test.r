t <- function(a, b=c('short','long','both'))
{
    print(a)
    print(match.arg(b))
}

t2 <- function()
{
    x = 1
    tt <- function(xx)
    {
        print(x)
        x=2
        print(x)
    }
    tt()
    print(x)
}

if (1==1)
{
    print(10)
} else
{
    print(0)
}

#t(1, 's')

#for (i in c(1,3,6.5,2)) print(i)
t2()
