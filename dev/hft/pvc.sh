indir=$1
outdir=$1

tmpana=$outdir/tmp
tmparrow=$outdir/tmp.arrow

cp pvchange2.plot $outdir
bmfn=$outdir/pvc.bm
rm $bmfn

for fn in $indir/siq20110915.log
#for fn in $indir/siq*.log
do
    bfn=`basename $fn .log`

    # analyzed data
    dfn=$outdir/$bfn.ana
    python pvchange.py $fn > $dfn

    # benchmarking
    afn=$outdir/$bfn.arrow
    echo $bfn
    echo $bfn >> $bmfn
    python pvbm.py $dfn > $afn 2>> $bmfn
    echo

    # plot
    cp $dfn $tmpana
    cp $afn $tmparrow

    pushd $outdir
    gnuplot pvchange2.plot
    mv tmp.ps $bfn.ps
    popd

    #mv $tmpana $dfn
    #mv $tmparrow $afn
done
