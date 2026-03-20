# ScreenTranslator Windows 打包脚本
# 使用方法: 在项目根目录运行 .\build\build_windows.ps1

param(
    [string]$Version = "0.1.0"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Set-Location $ProjectRoot
Write-Host "=== ScreenTranslator Windows 打包 v$Version ===" -ForegroundColor Cyan

# 安装依赖
Write-Host "`n[1/4] 安装依赖..." -ForegroundColor Yellow
pip install pyinstaller>=6.0 | Out-Null
pip install -r requirements.txt | Out-Null

# 清理旧构建
Write-Host "[2/4] 清理旧构建..." -ForegroundColor Yellow
if (Test-Path "dist\ScreenTranslator") { Remove-Item "dist\ScreenTranslator" -Recurse -Force }
if (Test-Path "build\__pycache__") { Remove-Item "build\__pycache__" -Recurse -Force }

# PyInstaller 打包
Write-Host "[3/4] 运行 PyInstaller..." -ForegroundColor Yellow
pyinstaller build\screen_translator.spec --noconfirm
if ($LASTEXITCODE -ne 0) { throw "PyInstaller 失败" }

# 创建 zip
Write-Host "[4/4] 创建压缩包..." -ForegroundColor Yellow
$ZipName = "ScreenTranslator-windows-$Version.zip"
$ZipPath = Join-Path "dist" $ZipName
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Compress-Archive -Path "dist\ScreenTranslator\*" -DestinationPath $ZipPath

Write-Host "`n=== 打包完成！===" -ForegroundColor Green
Write-Host "输出文件: dist\$ZipName" -ForegroundColor Green
Write-Host "可执行文件: dist\ScreenTranslator\ScreenTranslator.exe" -ForegroundColor Green
