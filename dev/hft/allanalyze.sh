for ((i=$1;i<=$2;i=i+2))
do
    for fn in $3/siq*.log
    do
        bfn=`basename $fn .log`
        dir=`dirname $fn`
        jstatfn=$dir/$bfn.jstat.$i
        python jitterstat.py $fn $i > $jstatfn
        jdistfn=$dir/$bfn.jdist.$i
        python jitterdist.py $jstatfn > $jdistfn
        jzcrossfn=$dir/$bfn.jzcrossdist.$i
        python jzcrossdist.py $jstatfn > $jzcrossfn
    done
done
