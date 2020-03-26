@echo off
setlocal

set HISCORE_DAT_PATH=..\plugins\hiscore\console_hiscore.dat
REM set HISCORE_PATH="R:\" 

python retroarch_hiscore_companion.py %*

pause
