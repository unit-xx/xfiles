set terminal postscript enhanced landscape
set output 'tmp.ps'

dfn = 'tmp'

set xtics 5
plot dfn using 1:2 with boxes title 'earn-hist'
