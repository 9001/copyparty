@echo off
rem Windows launcher for copyparty SFX files
rem Place this file next to your copyparty SFX .py file and double-click to run
rem 
rem This batch file:
rem - Finds and runs Python interpreter
rem - Sets PRTY_NO_MAGIC=1 to prevent crashes with python-magic
rem - Provides better error messages for Windows users
rem - Keeps the window open on errors for debugging

setlocal enabledelayedexpansion

rem Set environment variable to prevent segfaults
set PRTY_NO_MAGIC=1

cls
echo copyparty SFX Launcher for Windows
echo ================================
echo.

rem Look for .py file in the same directory
set "py_file="
for %%f in ("%~dp0*.py") do (
    set "py_file=%%f"
    goto found_py
)

:found_py
if "%py_file%"=="" (
    echo Error: No Python (.py) file found in this directory
    echo.
    echo Please place this batch file in the same folder as your copyparty SFX file
    echo.
    pause
    exit /b 1
)

echo Found SFX file: %py_file%

rem Find Python interpreter
set py=
echo Searching for Python interpreter...

rem Try python command first
python --version >nul 2>&1
if %errorlevel%==0 (
    set "py=python"
    goto run_sfx
)

rem Try py launcher
py --version >nul 2>&1
if %errorlevel%==0 (
    set "py=py"
    goto run_sfx
)

rem Search in PATH
for /f %%i in ('where python 2^>nul') do (
    set "py=%%i"
    goto run_sfx
)

rem Search in common locations
for %%p in (
    "c:\python39\python.exe"
    "c:\python38\python.exe" 
    "c:\python37\python.exe"
    "c:\python36\python.exe"
    "c:\python27\python.exe"
    "%localappdata%\programs\python\python39\python.exe"
    "%localappdata%\programs\python\python38\python.exe"
    "%localappdata%\programs\python\python37\python.exe"
) do (
    if exist %%p (
        set "py=%%p"
        goto run_sfx
    )
)

rem Search Windows Store Python
for /f %%i in ('where /r "%localappdata%\programs\python" python 2^>nul') do (
    set "py=%%i"
    goto run_sfx
)

echo Error: Could not find Python interpreter
echo.
echo Please install Python from https://python.org
echo Make sure to check "Add Python to PATH" during installation
echo.
echo Alternatively, you can run this command manually:
echo   python "%py_file%"
echo.
pause
exit /b 1

:run_sfx
echo Using Python: %py%
echo Setting PRTY_NO_MAGIC=1 to prevent crashes
echo.
echo Starting copyparty...
echo.

rem Run the Python file with all arguments passed to this batch file
"%py%" "%py_file%" %*

rem Check exit code
if %errorlevel%==0 (
    echo.
    echo copyparty finished successfully
) else (
    echo.
    echo copyparty exited with error code %errorlevel%
    echo.
    echo If you see "Segmentation fault" or similar crashes, this is likely
    echo caused by the python-magic library. The SFX file should automatically
    echo set PRTY_NO_MAGIC=1 to prevent this on Windows.
    echo.
    echo For more help, try running: 
    echo   "%py%" "%py_file%" --help
    echo.
    pause
)

endlocal
