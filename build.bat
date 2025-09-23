@echo off
cd /d "%~dp0"

REM ===== Configuração =====
set APP_NAME=GridX
set MAIN_FILE=data_science\app.py
set ICON_PATH="C:\Users\User\Documents\python_projects\python_projects\gridx.ico"

REM ===== Cria executável =====
echo [1/2] Limpando builds antigos...
rmdir /s /q build dist

echo [2/2] Gerando executável...
"..\.venv\Scripts\python.exe" -m PyInstaller --noconsole --onefile ^
  --name %APP_NAME% ^
  --icon %ICON_PATH% ^
  --hidden-import matplotlib.backends.backend_tkagg ^
  %MAIN_FILE%

echo.
echo ===== Build concluído =====
echo Executável em: dist\%APP_NAME%.exe
pause
