@echo off

REM setup conda env on my pc
call setconda

python.exe -mnuitka --follow-imports  retroarch_hiscore_companion.py
