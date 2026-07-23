@echo off
chcp 65001 >nul
title Building TestCaseGenerator.exe

echo ====================================
echo Construyendo TestCaseGenerator.exe
echo ====================================
echo.

REM Activar el venv si existe
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

echo Instalando dependencias...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo Limpiando builds anteriores...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

echo.
echo Compilando...
pyinstaller --onedir --windowed --name "TestCaseGenerator" ^
    --add-data "data;data" --add-data "assets;assets" ^
    --hidden-import "PIL._tkinter_finder" ^
    --icon assets\icon.ico ^
    APP.py

echo.
if exist dist\TestCaseGenerator (
    echo ====================================
    echo ✅ BUILD EXITOSO
    echo ====================================
    echo Ejecutable en: dist\TestCaseGenerator\TestCaseGenerator.exe
    echo.
    echo Para compartir, comprimi la carpeta dist\TestCaseGenerator\
    echo o usá --onefile en lugar de --onedir para un solo .exe
) else (
    echo ====================================
    echo ❌ BUILD FALLIDO
    echo ====================================
)

pause
