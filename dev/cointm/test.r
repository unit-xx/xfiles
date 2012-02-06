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

for (i in c(1,3,6.5,2)) print(i)
