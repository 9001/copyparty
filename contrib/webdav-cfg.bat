@echo off
rem removes the 47.6 MiB filesize limit when downloading from webdav
rem + optionally allows/enables password-auth over plaintext http
rem + optionally helps disable wpad, removing the 10sec latency

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo sorry, you must run this as administrator
    pause
    exit /b
)

reg add HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\services\WebClient\Parameters /v FileSizeLimitInBytes /t REG_DWORD /d 0xffffffff /f
reg add HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\WebClient\Parameters /v FsCtlRequestTimeoutInSec /t REG_DWORD /d 0xffffffff /f

echo(
echo OK;
echo allow webdav basic-auth over plaintext http?
echo Y: login works, but the password will be visible in wireshark etc
echo N: login will NOT work unless you use https and valid certificates
choice
if %errorlevel% equ 1 (
    reg add HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\services\WebClient\Parameters /v BasicAuthLevel /t REG_DWORD /d 0x2 /f
    rem default is 1 (require tls)
)

echo(
echo OK;
echo do you want to disable wpad?
echo can give a HUGE speed boost depending on network settings
choice
if %errorlevel% equ 1 (
    echo(
    echo i'm about to open the [Connections] tab in [Internet Properties] for you;
    echo please click [LAN settings] and disable [Automatically detect settings]
    echo(
    pause
    control inetcpl.cpl,,4
)

net stop webclient
net start webclient
echo(
echo OK; all done
pause
