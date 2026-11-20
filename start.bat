
@echo off
chcp 65001 > nul

cd /d "%~dp0"

call venv\Scripts\activate.bat

if errorlevel 1 (
    echo Не удалось активировать виртуальное окружение.
    pause
    exit /b 1
)

python run_local.py

pause
