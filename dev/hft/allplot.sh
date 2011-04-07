for ((i=$1;i<=$2;i=i+2))
do
    for fn in $3/siq*.log
    do
        bfn=`basename $fn .log`
        dir=`dirname $fn`
        jstatfn=$dir/$bfn.jstat.$i
        jdistfn=$dir/$bfn.jdist.$i
        jzcrossfn=$dir/$bfn.jzcrossdist.$i

        if [ ! -e $jdistfn.png ]
        then
            echo "gen $jdistfn"
            gnuplot <<EOF
            set terminal png
            set output "$jdistfn.png"
            set logscale y 2
            plot "$jdistfn" using 1:2 with boxes title "$jdistfn"
EOF
        fi

        if [ ! -e $jstatfn.png ]
        then
            echo "gen $jstatfn"
            gnuplot <<EOF
            set terminal png
            set output "$jstatfn.png"
            #set logscale y 2
            plot "$jstatfn" using 3:5 with boxes title "$jstatfn"
EOF
        fi

        jspreadfn=$dir/$bfn.jspread
        if [ ! -e $jspreadfn.png ]
        then
            echo "gen $jspreadfn"
            gnuplot <<EOF
            set terminal png
            set output "$jspreadfn.png"
            plot "$jstatfn" using 3:7 title "$jspreadfn"
EOF
        fi

        if [ ! -e $jzcrossfn.png ]
        then
            echo "gen $jzcrossfn"
            gnuplot <<EOF
            set terminal png
            set output "$jzcrossfn.png"
            plot "$jzcrossfn" using 1:2 with boxes title "$jzcrossfn"
EOF
        fi
    done
done
