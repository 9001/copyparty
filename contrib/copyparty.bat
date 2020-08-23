exec python "$(dirname "$0")"/copyparty.py

@rem on linux, the above will execute and the script will terminate
@rem on windows, the rest of this script will run

@echo off
cls

set py=
for /f %%i in ('where python 2^>nul') do (
    set "py=%%i"
    goto c1
)
:c1

if [%py%] == [] (
    for /f %%i in ('where /r "%localappdata%\programs\python" python 2^>nul') do (
        set "py=%%i"
        goto c2
    )
)
:c2

if [%py%] == [] set "py=c:\python27\python.exe"

if not exist "%py%" (
    echo could not find python
    echo(
    pause
    exit /b
)

start cmd /c %py% "%~dp0\copyparty.py"
