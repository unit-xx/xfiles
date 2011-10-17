set terminal postscript enhanced landscape color size 100,5

set grid
set ytics nomirror
set y2tics autofreq

set output 'volana.ps'

dfn = 'tmp'
plot dfn using 1:3 axis x1y2 with impulses, dfn using 1:4 axis x1y2 with line lt 1 lw 1 lc rgb 'blue', dfn using 1:($5+0) axis x1y2 with line, dfn using 1:($7*10) axis x1y2 with impulses lt 1 lw 1 lc rgb 'black', dfn using 1:2 with line lt 1 lc rgb 'cyan'
