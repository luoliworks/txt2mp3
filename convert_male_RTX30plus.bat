@echo off
call "%~dp0convert.bat" --voice "%~dp0examples\voice_05.wav" --bf16 %*
exit /b %errorlevel%
