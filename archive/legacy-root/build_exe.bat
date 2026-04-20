@echo off
setlocal

REM Simple helper to package the Ghost Companion launcher on Windows.
if "%~1"=="/h" goto :help
if "%~1"=="-h" goto :help

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

REM Ensure frontend dependencies are installed before bundling.
if not exist frontend\node_modules (
    echo Running npm install to prime the React app...
    pushd frontend
    npm install || exit /b 1
    popd
)

REM Build the frontend for production
echo Building frontend for production...
pushd frontend
npm run build || exit /b 1
popd

pyinstaller --clean --noconfirm ghost_companion.spec

echo.
echo Build complete. The executable lives in the dist\GhostCompanionLauncher folder.
goto :eof

:help
echo Usage: build_exe.bat
endlocal
