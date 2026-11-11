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

echo [1/2] Converting novel.txt to UTF-8...
uv run python txt2utf8.py
if errorlevel 1 (
    echo [ERROR] UTF-8 conversion failed.
    pause
    exit /b 1
)

echo.
echo [2/2] Splitting novel.txt into chapters (novel folder is recreated)...
uv run python split_novel.py
if errorlevel 1 (
    echo [ERROR] Splitting failed.
    pause
    exit /b 1
)

echo.
echo Done. Chapter files are in the novel folder.
pause
exit /b 0
