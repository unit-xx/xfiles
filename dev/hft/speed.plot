set terminal postscript enhanced landscape color size 30,5

stkspeed = 'stkspeed.12'
siqana = 'siqana'

set xdata time
set timefmt "%H:%M:%S"

set output "speedana.ps"

set grid
set lmargin 0
set rmargin 0
set ytics nomirror

set multiplot

set size 1,0.5
set origin 0.0,0.5
set xrange ["9:35:00":"11:25:00"]
#plot stkspeed using 2:($3*5) with line title '1st stk-speed', stkspeed using 2:($12*5) with line title '-1st stk-speed', siqana using 2:4 with line title 'siq-speed'

plot stkspeed using 2:(($3+$4+$5)*3) with line title 'increase', stkspeed using 2:(($10+$11+$12)*3) with line title 'decrease', siqana using 2:4 with line title 'siq-speed', siqana using 2:9 axis x1y2 with line title 'siqprice'

#plot stkspeed using 2:(($3+$4+$5+$6+$7)*1) with line title 'added', siqana using 2:4 with line title 'siq-speed'

set size 1,0.5
set origin 0.0,0.0
set xrange ["13:05:00":"14:55:00"]
plot stkspeed using 2:($3*5) with line title '1st stk-speed', stkspeed using 2:($12*5) with line title '-1st stk-speed', siqana using 2:4 with line title 'siq-speed'

unset multiplot
