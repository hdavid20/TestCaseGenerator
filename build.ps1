$ErrorActionPreference = "Stop"

Write-Host "===================================="
Write-Host "Construyendo TestCaseGenerator.exe"
Write-Host "===================================="
Write-Host ""

if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
}

Write-Host "Instalando dependencias..."
python -m pip install -r requirements.txt
python -m pip install -U pyinstaller

Write-Host ""
Write-Host "Limpiando builds anteriores..."
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

$pyArgs = @(
    "--onedir",
    "--windowed",
    "--name", "TestCaseGenerator",
    "--add-data", "data;data"
)

if (Test-Path "assets") {
    $pyArgs += "--add-data"
    $pyArgs += "assets;assets"
}

$pyArgs += "--hidden-import"
$pyArgs += "PIL._tkinter_finder"
$pyArgs += "--hidden-import"
$pyArgs += "fitz"
$pyArgs += "--hidden-import"
$pyArgs += "pymupdf"

$iconFile = Get-ChildItem "assets" -Filter "*.ico" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($iconFile) {
    $pyArgs += "--icon"
    $pyArgs += $iconFile.FullName
}

$pyArgs += "APP.py"

Write-Host ""
Write-Host "Compilando..."
python -m PyInstaller @pyArgs

Write-Host ""
if (Test-Path "dist\TestCaseGenerator") {
    Write-Host "===================================="
    Write-Host "BUILD EXITOSO"
    Write-Host "===================================="
    Write-Host "Ejecutable en: dist\TestCaseGenerator\TestCaseGenerator.exe"
} else {
    Write-Host "===================================="
    Write-Host "BUILD FALLIDO"
    Write-Host "===================================="
}
