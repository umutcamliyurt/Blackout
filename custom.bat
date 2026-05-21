@echo off
set LOG_FILE=%~dp0shutdown_log.txt

for /f "tokens=1-4 delims=/:. " %%a in ("%date% %time%") do (
    set TIMESTAMP=%%a-%%b-%%c %%d:%%e:%%f
)

echo [%TIMESTAMP%] Heartbeat lost. custom.bat triggered before shutdown. >> "%LOG_FILE%"