@echo off
rem removes the 47.6 MiB filesize limit when downloading from webdav

at > nul
if %errorlevel% neq 0 (
    echo you must run this as admin
    pause
    exit /b 1
)

reg add HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\services\WebClient\Parameters /v FileSizeLimitInBytes /t REG_DWORD /d 0xffffffff /f
reg add HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\WebClient\Parameters /v FsCtlRequestTimeoutInSec  /t REG_DWORD /d 0xffffffff /f
net stop WEBCLIENT
net start WEBCLIENT
pause
