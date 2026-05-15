@echo off
REM Inicia a interface web do projeto com HTTPS local (mic funciona no celular)
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set HF_HUB_DISABLE_SYMLINKS=1
if exist "certs\cert.pem" (
    echo Iniciando com HTTPS local em https://localhost:8501
    ".venv\Scripts\python.exe" -m streamlit run src\app.py ^
        --server.headless=true ^
        --server.port=8501 ^
        --server.sslCertFile=certs\cert.pem ^
        --server.sslKeyFile=certs\key.pem
) else (
    echo HTTPS nao configurado. Iniciando em HTTP simples...
    ".venv\Scripts\python.exe" -m streamlit run src\app.py --server.headless=true --server.port=8501
)
pause
