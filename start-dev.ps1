$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $RootDir "flet-app"
$FrontendDir = Join-Path $RootDir "react-new"

$ApiHost = if ($env:API_HOST) { $env:API_HOST } else { "127.0.0.1" }
$ApiPort = if ($env:API_PORT) { $env:API_PORT } else { "8000" }
$UiPort = if ($env:UI_PORT) { $env:UI_PORT } else { "5173" }

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Error "python is required but was not found in PATH."
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
  Write-Error "npm is required but was not found in PATH. Install Node.js from https://nodejs.org/"
}

if (-not (Test-Path (Join-Path $BackendDir "requirements.txt"))) {
  Write-Error "Missing backend requirements file in $BackendDir"
}

if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
  Write-Host "react-new/node_modules not found. Running npm install..."
  Push-Location $FrontendDir
  npm install
  Pop-Location
}

Write-Host "Starting backend on http://$ApiHost`:$ApiPort ..."
Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "Set-Location '$BackendDir'; python -m uvicorn api_main:app --host $ApiHost --port $ApiPort"
)

Write-Host "Starting frontend on http://localhost:$UiPort ..."
Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "`$env:API_PROXY_TARGET='http://$ApiHost`:$ApiPort'; Set-Location '$FrontendDir'; npm run dev"
)

Write-Host "Launched backend and frontend in separate windows."
Write-Host "Close those windows to stop the servers."
