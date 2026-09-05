@echo off
cd /d "%~dp0"
echo Checking dependencies...
python -m pip install -r requirements.txt --quiet --disable-pip-version-check
echo Starting Basket Sorter Vision...
powershell -NoProfile -Command "python -u gui.py 2>&1 | Tee-Object -FilePath 'gui_console.log'"
if errorlevel 1 (
    echo.
    echo The application exited with an error. See the message above.
    pause
)
