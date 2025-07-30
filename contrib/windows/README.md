# Windows Support for copyparty SFX Files

This directory contains Windows-specific tools and solutions for running copyparty SFX (self-extracting) files.

## Problem

Windows users often experience issues when trying to run copyparty SFX files:

1. **Double-click doesn't work**: Clicking on `.py` files may open an editor instead of running the script
2. **Segmentation faults**: The python-magic library can cause crashes on Windows
3. **Poor error messages**: When something goes wrong, users don't get helpful feedback

## Solutions

### Option 1: Use the SFX Launcher (Recommended)

1. Download `run-sfx.bat` and place it in the same folder as your copyparty SFX file
2. Double-click `run-sfx.bat` instead of the `.py` file
3. The launcher will:
   - Automatically find your Python installation
   - Set `PRTY_NO_MAGIC=1` to prevent crashes
   - Provide helpful error messages
   - Keep the window open so you can see what happened

### Option 2: Create a Paired Batch File

1. Download `copyparty-sfx.bat` 
2. Rename it to match your SFX file (e.g., `copyparty-1.8.5.py` → `copyparty-1.8.5.bat`)
3. Double-click the `.bat` file instead of the `.py` file

### Option 3: Manual Environment Variable

If you prefer to run the SFX file directly:

1. Open Command Prompt or PowerShell
2. Set the environment variable: `set PRTY_NO_MAGIC=1`
3. Run: `python copyparty-x.x.x.py`

### Option 4: Fix File Association

Associate `.py` files with Python interpreter:

1. Right-click any `.py` file → "Open with" → "Choose another app"
2. Browse to your Python installation (e.g., `C:\Python39\python.exe`)
3. Check "Always use this app to open .py files"

## Files in this Directory

- `copyparty-sfx.bat` - Generic batch file template for any SFX file
- `run-sfx.bat` - Universal SFX launcher that finds any `.py` file in the same directory
- `copyparty-ctmp.bat` - Existing utility for running copyparty.exe with fixed temp directory

## Technical Details

The SFX script automatically sets `PRTY_NO_MAGIC=1` on Windows to disable the python-magic library, which is known to cause segmentation faults on Windows systems. This environment variable is checked by copyparty to determine whether to use python-magic for file type detection.

## Troubleshooting

If you still have issues:

1. Make sure Python is installed and accessible from the command line
2. Try running `python --version` in Command Prompt to verify
3. Check that you have the latest copyparty SFX file
4. For advanced debugging, run the SFX file from Command Prompt to see detailed error messages

## Related Issues

- [#324: Windows users can't double-click SFX files](https://github.com/9001/copyparty/issues/324)
- [#325: ShareX v17+ compatibility](https://github.com/9001/copyparty/issues/325)
