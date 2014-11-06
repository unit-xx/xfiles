rem set folder=%1

setlocal 
set fn=%~n1
set dirn=%~dp1

rem echo %dirn%
rem echo %fn%
rem echo %dirn%xxx

rscript scpbmperf.R %dirn%%fn%.qhist %dirn%%fn%.bmrpt

