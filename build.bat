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
python -m pip install -r requirements.txt
python -m pip install -U pyinstaller

echo.
echo Limpiando builds anteriores...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

REM Agregar assets solo si existen
set "ADD_DATA="
if exist assets (
    set "ADD_DATA=--add-data "assets;assets" "
)

set "ICON_ARG="
for %%f in (assets\*.ico) do set "ICON_ARG=--icon "%%f" "

echo.
echo Compilando...
python -m PyInstaller --onedir --windowed --name "TestCaseGenerator" --add-data "data;data" %ADD_DATA%--hidden-import "PIL._tkinter_finder" --hidden-import "fitz" --hidden-import "pymupdf" %ICON_ARG%APP.py

echo.
if exist dist\TestCaseGenerator (
    echo ====================================
    echo BUILD EXITOSO
    echo ====================================
    echo Ejecutable en: dist\TestCaseGenerator\TestCaseGenerator.exe
    echo.
    echo Para compartir, comprimi la carpeta dist\TestCaseGenerator\
    echo o usá --onefile en lugar de --onedir para un solo .exe
) else (
    echo ====================================
    echo BUILD FALLIDO
    echo ====================================
)

pause
