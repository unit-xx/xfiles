rem set folder=%1

setlocal 
set fn=%~n1
set dirn=%~dp1

rem echo %dirn%
rem echo %fn%
rem echo %dirn%xxx

python scpstat.py %1 %dirn%%fn%.stat
rscript scpstat.r %dirn%%fn%.stat %dirn%%fn%.stat.pdf
