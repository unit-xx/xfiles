rem set folder=%1

setlocal 
set fn=%~n1
set dirn=%~dp1

rem echo %dirn%
rem echo %fn%
rem echo %dirn%xxx

if "%2"=="new" (
python scpcontext.py %dirn%%fn%.trace %dirn%%fn%.qhist %dirn%%fn%.thist
)
rscript scprevtrd.R %dirn%%fn%.qhist %dirn%%fn%.thist %dirn%%fn%.trdrpt

