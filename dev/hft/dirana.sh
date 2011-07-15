logdir=$1
outputdir=$2

rm $outputdir/dirbm.rst
for fn in $logdir/siq*.log
do
    python dirana.py 30 $fn > $logdir/tmp
    echo $fn >> $outputdir/dirbm.rst
    python dirbm.py $logdir/tmp >> $outputdir/dirbm.rst
done
