@echo off
REM Inicia a interface web do projeto
cd /d "%~dp0"
".venv\Scripts\python.exe" -m streamlit run src\app.py
pause
