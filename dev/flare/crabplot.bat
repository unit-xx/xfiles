python crablog.py .\%1\crabstrat2.log .\%1\crabstrat2.log2
python crabplot.py full .\%1\crabstrat2.log2 50 .\%1\50hist
rscript crabplot.r .\%1\50hist .\%1\50.pdf
