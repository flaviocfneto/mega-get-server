@echo off
setlocal enabledelayedexpansion

set "ROOT_DIR=%~dp0"
set "BACKEND_DIR=%ROOT_DIR%api"
set "FRONTEND_DIR=%ROOT_DIR%web"

if "%API_HOST%"=="" set "API_HOST=127.0.0.1"
if "%API_PORT%"=="" set "API_PORT=8000"
if "%UI_PORT%"=="" set "UI_PORT=5173"

where python >nul 2>nul
if errorlevel 1 (
  echo python is required but was not found in PATH.
  exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
  echo npm is required but was not found in PATH.
  echo Install Node.js from https://nodejs.org/
  exit /b 1
)

if not exist "%BACKEND_DIR%\requirements.txt" (
  echo Missing backend requirements file at "%BACKEND_DIR%\requirements.txt"
  exit /b 1
)

if not exist "%FRONTEND_DIR%\node_modules" (
  echo web\node_modules not found. Running npm install...
  pushd "%FRONTEND_DIR%"
  call npm install
  if errorlevel 1 (
    popd
    exit /b 1
  )
  popd
)

echo Starting backend on http://%API_HOST%:%API_PORT% ...
start "mega-get backend" cmd /k "cd /d ""%BACKEND_DIR%"" && python -m uvicorn api_main:app --host %API_HOST% --port %API_PORT%"

echo Starting frontend on http://localhost:%UI_PORT% ...
start "mega-get frontend" cmd /k "cd /d ""%FRONTEND_DIR%"" && set API_PROXY_TARGET=http://%API_HOST%:%API_PORT%&& npm run dev"

echo Launched backend and frontend in separate windows.
echo Close those windows to stop the servers.
exit /b 0
