
n = 0.0
t1 = Sys.time()
for (i in 1:10000)
{
  a = runif(1)
  c = (a>n)
}
t2 = Sys.time()

sec = as.double(t2-t1)
print(c(sec, sec/10000, 10000/sec))

t1 = Sys.time()
a = runif(10000)
c = (a>n)
t2 = Sys.time()

sec = as.double(t2-t1)
print(c(sec, sec/10000, 10000/sec))
