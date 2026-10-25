@echo off
setlocal
cd /d "%~dp0"
set "CG_PY=%~dp0.venv\Scripts\python.exe"
if defined CONTEXTGUARD_PYTHON goto external_python
if exist "%CG_PY%" goto check_python
where py >nul 2>&1
if errorlevel 1 goto system_python
py -3 -c "import operator,sys; raise SystemExit(operator.lt(sys.version_info,(3,11)))" >nul 2>&1
if errorlevel 1 goto system_python
echo [ContextGuard] Creating the local Python environment...
py -3 -m venv .venv
if errorlevel 1 goto fail
goto check_python
:system_python
where python >nul 2>&1
if errorlevel 1 goto no_python
python -c "import operator,sys; raise SystemExit(operator.lt(sys.version_info,(3,11)))" >nul 2>&1
if errorlevel 1 goto no_python
echo [ContextGuard] Creating the local Python environment...
python -m venv .venv
if errorlevel 1 goto fail
goto check_python
:external_python
set "CG_PY=%CONTEXTGUARD_PYTHON%"
if not exist "%CG_PY%" (
  echo CONTEXTGUARD_PYTHON does not point to an existing Python executable.
  goto fail
)
:check_python
"%CG_PY%" -c "import operator,sys; raise SystemExit(operator.lt(sys.version_info,(3,11)))" >nul 2>&1
if errorlevel 1 goto broken
"%CG_PY%" scripts\launcher.py %*
if errorlevel 1 goto fail
exit /b 0
:no_python
echo Python 3.11 or newer is required. Install it and run start.bat again.
goto fail
:broken
echo The selected Python cannot run or is older than 3.11. It has been preserved.
echo Rename .venv to .venv-backup and run start.bat again.
:fail
echo The requested setup, startup or verification step did not complete.
echo Read the error above. No reviews were deleted.
if not "%CONTEXTGUARD_NO_PAUSE%"=="1" pause
exit /b 1
