@echo off
REM Roda o processador continuo (le queue.txt e processa videos)
cd /d "%~dp0"
".venv\Scripts\python.exe" src\daemon.py 300
pause
