set terminal postscript enhanced landscape color size 20,5

set size 1,1
set grid
set lmargin 0
set rmargin 0
set output "tmp.ps"
set ytics nomirror
set y2tics autofreq
set xtics 3000

dfn = 'tmp'

set multiplot

set xrange [0:]

set size 1,0.75
set origin 0.0, 0.0
load 'tmp.arrow'
#set y2range [-2e-6:2e-6]
plot dfn using 1:2 with line title 'pp' lt 1 lc rgb 'pink', dfn using 1:3 with line title 'pp2' lt 1 lc rgb 'red', dfn using 1:($7) axis x1y2 with line lt 1 lc rgb 'green' title 'pchange2-ef2', dfn using 1:($8) axis x1y2 with line lt 1 lc rgb 'blue' title 'pchange2-ef3', dfn using 1:($9) axis x1y2 with line lt 1 lc rgb 'purple' title 'pchange2-ef3', dfn using 1:($10) axis x1y2 with line lt 1 lw 2 lc rgb 'dark-grey' title 'pchange2-ef4', dfn using 1:(0) axis x1y2 with line lt 1 lc rgb 'black' notitle


#dfn using 1:7 axis x1y2 with line lt 1 lc rgb 'green' title 'pchange2-ef',

# dfn using 1:($7-$8) axis x1y2 with line lc rgb 'blue' title 'ef-diff'
# dfn using 1:8 axis x1y2 with line lt 1 lc rgb 'blue' title 'pchange2-ef2'

#dfn using 1:2 with line title 'pp' lt 1 lc rgb 'black',

set size 1, 0.25
set origin 0.0, 0.75
set yrange [0:5]
plot dfn using 1:($11/$12) with line title 'evpp2'
#plot dfn using 1:10 with line title 'evpp2', dfn using 1:11 with line title 'evem'
