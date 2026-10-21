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

echo [1/4] Converting novel.txt to UTF-8...
uv run python txt2utf8.py
if errorlevel 1 (
    echo [ERROR] UTF-8 conversion failed.
    pause
    exit /b 1
)

echo.
echo [2/4] Clearing novel folder...
if exist "novel" rmdir /s /q "novel"
if exist "novel" goto clear_error

echo.
echo [3/4] Splitting novel.txt into chapters...
uv run python split_novel.py
if errorlevel 1 (
    echo [ERROR] Splitting failed.
    pause
    exit /b 1
)

echo.
echo [4/4] Converting chapters to MP3...
uv run python txt2mp3.py %*
if errorlevel 1 (
    echo [ERROR] Conversion failed.
    pause
    exit /b 1
)

echo.
echo Done. MP3 files are in the mp3 folder.
pause
exit /b 0

:clear_error
echo [ERROR] Could not clear the novel folder. Close any program using those files and try again.
pause
exit /b 1
