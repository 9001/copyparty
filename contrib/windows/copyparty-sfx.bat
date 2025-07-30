@echo off
rem Batch file to run copyparty SFX files on Windows
rem This solves the issue where double-clicking .py files doesn't work properly
rem
rem Usage: 
rem   1. Copy this file to the same folder as your copyparty SFX file
rem   2. Rename this file to match your SFX file (e.g., copyparty-1.8.5.py -> copyparty-1.8.5.bat)  
rem   3. Double-click the .bat file instead of the .py file
rem
rem Alternatively, associate .py files with this batch file in Windows

setlocal

rem Set PRTY_NO_MAGIC to prevent segmentation faults with python-magic on Windows
set PRTY_NO_MAGIC=1

rem Clear screen for better user experience
cls

rem Find the corresponding .py file
set "sfx_file=%~dpn0.py"

if not exist "%sfx_file%" (
    echo Error: Could not find %sfx_file%
    echo.
    echo This batch file should have the same name as your copyparty SFX file.
    echo For example, if your SFX file is "copyparty-1.8.5.py", 
    echo rename this batch file to "copyparty-1.8.5.bat"
    echo.
    pause
    exit /b 1
)

rem Try to find Python interpreter
set py=
for /f %%i in ('where python 2^>nul') do (
    set "py=%%i"
    goto found_python
)

rem Check Windows Store Python location
for /f %%i in ('where /r "%localappdata%\programs\python" python 2^>nul') do (
    set "py=%%i"
    goto found_python
)

rem Check common Python locations
if exist "c:\python39\python.exe" set "py=c:\python39\python.exe" && goto found_python
if exist "c:\python38\python.exe" set "py=c:\python38\python.exe" && goto found_python
if exist "c:\python37\python.exe" set "py=c:\python37\python.exe" && goto found_python
if exist "c:\python27\python.exe" set "py=c:\python27\python.exe" && goto found_python

echo Error: Could not find Python interpreter
echo.
echo Please install Python from https://python.org
echo or make sure Python is in your PATH environment variable
echo.
pause
exit /b 1

:found_python
echo Starting copyparty SFX: %sfx_file%
echo Using Python: %py%
echo.

rem Run the SFX file
"%py%" "%sfx_file%" %*

rem Keep window open if there was an error
if errorlevel 1 (
    echo.
    echo copyparty SFX exited with error code %errorlevel%
    pause
)

endlocal
