t1 = Sys.time()

ttrace = data.frame(stringsAsFactors=F)
cc = c()
bb = c()
a = as.data.frame(index(dq1))
lena = NROW(a)
b = 1:lena
c = 1:lena
i = 0
while (i < lena)
{
  i = i + 1
  #ttrace = rbind(ttrace, as.data.frame(list(a=i, b=i, c=i)))
  #b = b+1
  b[i] < 4
  #bb = c(bb, i)
}

t2 = Sys.time()

t2 - t1