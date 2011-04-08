lcdir=$1
outputdir=$2

for fn in $lcdir/siq*.lc
do
    bfn=`basename $fn .lc`
    gnuplot <<EOF
    set terminal png size 1280,768
    set output "$outputdir/$bfn.lc.png"
    plot "$fn" using 3 with lp title "$bfn"
EOF
done
