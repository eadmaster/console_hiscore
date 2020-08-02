@echo off
setlocal

set HISCORE_DAT_PATH=..\plugins\hiscore\console_hiscore.dat
REM set HISCORE_PATH="R:\" 

REM python retroarch_hiscore_companion.py %*
retroarch_hiscore_companion.exe %*

pause
