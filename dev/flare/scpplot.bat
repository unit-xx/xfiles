rem set folder=%1

setlocal 
set fn=%~n1
set dirn=%~dp1

rem echo %dirn%
rem echo %fn%
rem echo %dirn%xxx

if "%2"=="new" (
python scplog.py %1 %dirn%%fn%.trace
python scpplot.py full %dirn%%fn%.trace 200 %dirn%%fn%.frame
)
rscript crabplot.r %dirn%%fn%.frame %dirn%%fn%.trace.pdf
