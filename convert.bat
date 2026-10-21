@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"

where uv >nul 2>nul
if errorlevel 1 (
    echo [ERROR] uv was not found in PATH.
    pause
    exit /b 1
)

if not exist "novel.txt" (
    echo [ERROR] novel.txt was not found in this folder.
    pause
    exit /b 1
)

echo [1/2] Splitting novel.txt into chapters...
uv run python split_novel.py
if errorlevel 1 (
    echo [ERROR] Splitting failed.
    pause
    exit /b 1
)

echo.
echo [2/2] Converting chapters to MP3...
uv run python txt2mp3.py %*
if errorlevel 1 (
    echo [ERROR] Conversion failed.
    pause
    exit /b 1
)

echo.
echo Done. MP3 files are in the mp3 folder.
pause
