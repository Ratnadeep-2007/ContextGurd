@echo off
setlocal
cd /d "%~dp0"
where node >nul 2>&1
if errorlevel 1 goto no_node
node -e "if(Number(process.versions.node.split('.')[0])<20)process.exit(1)"
if errorlevel 1 goto no_node
echo Installing the pinned experimental WhatsApp reader. No account is linked by setup.
call npm.cmd install --prefix connectors\whatsapp --cache artifacts\npm-cache --omit=dev --no-audit --no-fund --fetch-retries=0 --fetch-timeout=20000
if errorlevel 1 goto failed
node connectors\whatsapp\check.mjs
if errorlevel 1 goto failed
if not exist ".venv\Scripts\python.exe" (
  echo Run start.bat once to set up Python, then rerun setup-whatsapp.bat.
  exit /b 1
)
".venv\Scripts\python.exe" scripts\check_whatsapp_protection.py
if errorlevel 1 exit /b 1
echo Ready. Open Sources, refresh WhatsApp status, then choose Pair / reconnect.
echo Linking requires your consent and a QR scan from your phone.
exit /b 0
:no_node
echo Install Node.js 20 or newer, then run setup-whatsapp.bat again.
exit /b 1
:failed
echo WhatsApp dependencies could not be installed or loaded. Check network access and retry.
echo Manual chat import remains available. No account was linked.
exit /b 1
