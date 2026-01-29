@echo off
setlocal

REM Simple helper to package the Ghost Companion on Windows.
if "%~1"=="/h" goto :help
if "%~1"=="-h" goto :help
if "%~1"=="--help" goto :help

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if "%~1"=="--desktop" goto :desktop

REM Default: build the web+backend launcher
call :build_frontend
pyinstaller --clean --noconfirm ghost_companion.spec || exit /b 1
echo.
echo Build complete. The launcher EXE is in dist\GhostCompanionLauncher
goto :eof

:desktop
echo Building desktop app (no browser UI)...
call :build_frontend
pyinstaller --clean --noconfirm ghost_desktop.spec || exit /b 1
echo.
echo Build complete. The desktop EXE is in dist\GhostCompanion
goto :eof

:build_frontend
REM Ensure frontend dependencies are installed before bundling.
if not exist frontend\node_modules (
    echo Running npm install to prime the React app...
    pushd frontend
    npm install || exit /b 1
    popd
)
echo Building frontend for production...
pushd frontend
npm run build || exit /b 1
popd
exit /b 0

:help
echo Usage: build_exe.bat [--desktop]
endlocal
