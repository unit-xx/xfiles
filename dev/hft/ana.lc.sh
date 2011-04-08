logdir=$1
outputdir=$2

for fn in $logdir/siq*.log
do
    bfn=`basename $fn .log`
    python siflc.py $fn > $outputdir/$bfn.lc
done
