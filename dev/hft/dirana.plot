set terminal postscript enhanced landscape color size 100,5
#set terminal pdf color size 100, 5
set size 1, 1
set grid
set lmargin 0
set rmargin 0
set output "tmp.ps"
set multiplot
set xtics 200
set size 1,0.5
set origin 0.0, 0.0
set ytics nomirror
set y2tics autofreq
#plot 'tmp' every ::6000::7000 using 1:3 with line  title 'corr', 'tmp' every ::6000::7000 using 1:($2*10) with line title 'beta x 10', 'tmp' every ::6000::7000 using 1:(0) with line title 'zerobeta'
#load 'tmp.arrow'
plot [0:]  'tmp' using 1:3 axis x1y2 with line title 'corr', 'tmp' using 1:2 with line title 'beta', 'tmp' using 1:4 with line title 'beta-long', 'tmp' using 1:(tan(2*atan($4)-atan($2))) with line title 'beta-delayed', 'tmp' using 1:(0) with line lt 1 lc rgb 'red' notitle

# 'tmp' using 1:(0) axis x1y2 with line lc rgb 'red' notitle

# 'tmp' using 1:($2*50) with line title 'beta x50'
# 'tmp' using 1:13 axis x1y2 with line title 'beta(beta,corr)'
# 'tmp' using 1:14 with line title 'corr(beta,corr)'
# 'tmp' using 1:12 with impulses lc rgb 'dark-cyan' title 'bid-ask', 
# 'tmp' using 1:($4*10) with line title 'beta x10-MA', 

set size 1,0.5
set origin 0.0, 0.5
#set logscale y
set ytics 5
#set mytics 5
#set yrange [185:200]
#plot 'tmp' every ::6000::7000 using 1:($5-2700) with line title 'price'
#load 'tmp.arrow'
plot [0:] 'tmp' using 1:8 axis x1y2 with impulses lt 1 lc rgb 'cyan' title 'dv', 'tmp' using 1:(20*$10/$9) axis x1y2 with line title '20 x dv-MA/dv-20minMA' lc rgb 'blue', 'tmp' using 1:7 with line title 'price' lc rgb 'black' lt 1

# 'tmp' using 1:7 axis x1y2 with line lc rgb 'purple' title 'dv-MA', 
# 'tmp' using 1:6 axis x1y2 with impulses lt 1 lc rgb 'cyan' title 'dv', 
# 'tmp' using 1:($8+$7) axis x1y2 with line title 'dv-SIGMA.UP',
# 'tmp' using 1:(-$8+$7) axis x1y2 with line title 'dv-SIGMA.DOWN',
unset multiplot
