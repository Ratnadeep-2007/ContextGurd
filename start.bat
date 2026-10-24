@echo off
setlocal EnableExtensions
title ContextGuard

rem ============================================================
rem  ContextGuard one-click launcher (Windows)
rem  First run : creates .venv, installs Python packages and
rem              builds the web UI automatically.
rem  Later runs: starts straight away and opens the browser.
rem  Any failure stays on screen so you can read what to fix.
rem ============================================================

cd /d "%~dp0" || (
  echo [ContextGuard] Could not open the project folder "%~dp0".
  pause
  exit /b 1
)

set "VENV_PY=%~dp0.venv\Scripts\python.exe"
set "FAILCODE=1"

rem ------------------------------------------------------------
rem 1. Python virtual environment (.venv)
rem ------------------------------------------------------------
if exist "%VENV_PY%" (
  "%VENV_PY%" --version >nul 2>&1
  if not errorlevel 1 goto :venv_ok
  echo [ContextGuard] The existing .venv looks broken. Recreating it...
  rmdir /s /q "%~dp0.venv" >nul 2>&1
)

echo [ContextGuard] First-time setup 1 of 3: creating Python environment...
call :find_base_python
if not defined BASE_PY_CMD goto :no_python
"%BASE_PY_CMD%" -m venv "%~dp0.venv"
if errorlevel 1 (
  echo [ContextGuard] Could not create the .venv folder.
  echo Check free disk space and folder permissions, then run start.bat again.
  goto :fail
)

:venv_ok
rem ------------------------------------------------------------
rem 2. Python dependencies
rem ------------------------------------------------------------
"%VENV_PY%" -c "import fastapi, uvicorn, pydantic, httpx, multipart, dotenv, pypdf, docx" >nul 2>&1
if not errorlevel 1 goto :deps_ok

echo [ContextGuard] First-time setup 2 of 3: installing Python packages...
"%VENV_PY%" -m pip install -r "%~dp0backend\requirements-tested.txt"
if errorlevel 1 (
  echo [ContextGuard] Package installation failed. Check your internet connection,
  echo then run start.bat again. Manual command:
  echo   .venv\Scripts\python.exe -m pip install -r backend\requirements-tested.txt
  goto :fail
)
"%VENV_PY%" -c "import fastapi, uvicorn, pydantic, httpx, multipart, dotenv, pypdf, docx" >nul 2>&1
if errorlevel 1 (
  echo [ContextGuard] Packages installed but still cannot be imported.
  echo Delete the .venv folder, then run start.bat again.
  goto :fail
)

:deps_ok
rem ------------------------------------------------------------
rem 3. Frontend build (frontend\dist)
rem ------------------------------------------------------------
if exist "%~dp0frontend\dist\index.html" goto :frontend_ok

echo [ContextGuard] First-time setup 3 of 3: building the web UI...
where node >nul 2>&1 || goto :no_node
where npm.cmd >nul 2>&1 || goto :no_node

pushd "%~dp0frontend" || goto :fail
if exist "node_modules" goto :build_frontend
call npm.cmd ci --no-fund --no-audit
if not errorlevel 1 goto :build_frontend
popd
echo [ContextGuard] Downloading web packages failed. Check your internet
echo connection, then run start.bat again. Manual commands:
echo   cd frontend ^& npm.cmd ci ^& npm.cmd run build
goto :fail

:build_frontend
call npm.cmd run build
if not errorlevel 1 goto :build_done
popd
echo [ContextGuard] The web UI build failed. Read the errors above.
echo Node.js 22.12 or newer is required. Then run start.bat again.
goto :fail

:build_done
popd
if exist "%~dp0frontend\dist\index.html" goto :frontend_ok
echo [ContextGuard] The build finished but frontend\dist\index.html is missing.
goto :fail

:frontend_ok
rem ------------------------------------------------------------
rem 4. Open the browser once healthy, then run the server.
rem    This window stays open while the app runs. Ctrl+C stops.
rem ------------------------------------------------------------
if /i not "%CONTEXTGUARD_NO_BROWSER%"=="1" call :open_browser_when_ready

"%VENV_PY%" "%~dp0scripts\serve.py"
set "FAILCODE=%errorlevel%"
if "%FAILCODE%"=="0" exit /b 0
echo [ContextGuard] The server stopped with code %FAILCODE%. See the message above.
goto :fail

rem ------------------------------------------------------------
rem Helpers
rem ------------------------------------------------------------
:find_base_python
set "BASE_PY_CMD="
where py >nul 2>&1 || goto :try_plain_python
py -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1 || goto :try_plain_python
set "BASE_PY_CMD=py"
goto :eof

:try_plain_python
where python >nul 2>&1 || goto :eof
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1 || goto :eof
set "BASE_PY_CMD=python"
goto :eof

:open_browser_when_ready
start "" /b powershell -NoProfile -WindowStyle Hidden -Command "for($i=0;$i -lt 40;$i++){try{$r=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8017/api/health' -TimeoutSec 1;if($r.StatusCode -eq 200){Start-Process 'http://localhost:8017';break}}catch{};Start-Sleep -Milliseconds 700}"
goto :eof

:no_python
echo.
echo [ContextGuard] Python 3.11 or newer was not found on this PC.
echo Install it from https://www.python.org/downloads/
echo Tick "Add python.exe to PATH" during setup, then run start.bat again.
echo Tip: if Python is installed but still not found, turn it on under
echo Windows Settings - Apps - Advanced app settings - App execution aliases.
goto :fail

:no_node
echo.
echo [ContextGuard] Node.js was not found, and the web UI is not built yet.
echo Install Node.js 22.12 or newer from https://nodejs.org/
echo Then run start.bat again - it will build the UI automatically.
goto :fail

:fail
echo.
echo [ContextGuard] Startup did not finish. Fix the issue above, then run start.bat again.
if /i not "%CONTEXTGUARD_NO_PAUSE%"=="1" pause
exit /b %FAILCODE%
