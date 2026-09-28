@echo off
setlocal
pushd "%~dp0"
python -u "%~dp0video_demo.py"
set "b07_exit=%errorlevel%"
popd
if not "%b07_exit%"=="0" (
    echo.
    echo The menu exited with code %b07_exit%. Check the message above.
    pause
)
exit /b %b07_exit%
