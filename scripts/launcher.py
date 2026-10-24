"""Windows launcher checks. No provider calls, source connections or secret output."""
import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
URL = 'http://127.0.0.1:8027'
IMPORTS = ('fastapi', 'uvicorn', 'pydantic', 'httpx', 'multipart', 'dotenv', 'pypdf', 'docx')


def instance_id(root=ROOT):
    return hashlib.sha256(str(root.resolve()).casefold().encode()).hexdigest()[:12]


def probe(url=URL, expected=None):
    parsed = urllib.parse.urlsplit(url)
    try:
        with socket.create_connection((parsed.hostname, parsed.port), timeout=0.5):
            pass
    except OSError:
        return 'free', None
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(url + '/api/health', timeout=2) as response:
            body = json.loads(response.read(4096))
        if body.get('product') == 'ContextGuard' and body.get('version') == 'rebuild' and body.get('instance_id') == (expected or instance_id()):
            return 'ours', body
    except (OSError, ValueError, urllib.error.URLError):
        pass
    return 'occupied', None


def ensure_env(root=ROOT):
    target = root / '.env'
    if not target.exists():
        with target.open('x', encoding='utf-8') as output:
            output.write((root / '.env.example').read_text(encoding='utf-8'))
        print('[Setup] Created a secret-free .env. Existing settings are never overwritten.', flush=True)


def missing_dependencies(root=ROOT):
    missing = []
    for line in (root / 'requirements.txt').read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        name, version = line.strip().split('==', 1)
        try:
            installed = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            installed = None
        if installed != version:
            missing.append(name)
    try:
        for module in IMPORTS:
            importlib.import_module(module)
    except Exception:
        if not missing:
            missing.append('runtime imports')
    return missing


def install_dependencies(root=ROOT):
    base = [sys.executable, '-m', 'pip', 'install', '-r', str(root / 'requirements.txt')]
    wheels = root / 'artifacts/wheels'
    if wheels.is_dir() and any(wheels.glob('*.whl')):
        print('[Setup] Installing pinned dependencies from available cached wheels...', flush=True)
        result = subprocess.run(base + ['--no-index', '--find-links', str(wheels)], capture_output=True, timeout=180)
        if result.returncode == 0:
            return True
    print('[Setup] Installing pinned dependencies; package download access is required...', flush=True)
    result = subprocess.run(base, capture_output=True, timeout=180)
    if result.returncode:
        print('[Setup] Dependency installation failed. Check internet/proxy settings, then run this manually:', flush=True)
        print('  .venv\\Scripts\\python.exe -m pip install -r requirements.txt', flush=True)
        # Never dump package-manager output, which may include private index URLs.
        return False
    return True


def settings_status(root=ROOT):
    from dotenv import dotenv_values
    values = {**dotenv_values(root / '.env'), **os.environ}
    present = lambda *names: all(bool(values.get(name)) for name in names)
    return {
        'Muse Wonder': present('MODEL_API_KEY', 'MODEL_BASE_URL', 'MODEL_NAME'),
        'Groq fallback': present('GROQ_API_KEY'),
        'NVIDIA fallback': present('NVIDIA_API_KEY', 'NVIDIA_MODEL'),
        'Vexa': present('VEXA_API_KEY'),
        'Slack OAuth': present('SLACK_CLIENT_ID', 'SLACK_CLIENT_SECRET'),
        'Slack local token': present('SLACK_BOT_TOKEN', 'SLACK_TEAM_ID'),
    }


def show_status(root=ROOT):
    print('[Ready] Python and pinned application dependencies are installed.', flush=True)
    for name, configured in settings_status(root).items():
        print(f'  {name}: ' + ('configured locally; live access not verified' if configured else 'not configured'), flush=True)
    print('  WhatsApp: manual/test import only; live Baileys pairing is disabled.', flush=True)
    print('Fictional sample/manual input work without model or connector keys.', flush=True)
    print('No external account is contacted during these setup checks.', flush=True)


def open_when_ready():
    for _ in range(80):
        state, health = probe()
        if state == 'ours':
            print('[Ready] ' + URL, flush=True)
            if health.get('setup_required'):
                print('Create your local owner account in the browser, then try the fictional sample.', flush=True)
            if os.getenv('CONTEXTGUARD_NO_BROWSER') != '1':
                try:
                    webbrowser.open(URL)
                except Exception:
                    print('Open the URL above in your browser.', flush=True)
            return
        time.sleep(0.25)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Show local setup status without starting the server')
    args = parser.parse_args(argv)
    os.chdir(ROOT)
    ensure_env()
    state, health = probe()
    if not args.check and state == 'occupied':
        print('Port 8027 belongs to another process or an older app instance. Close that window or use its existing URL. No process was stopped.', flush=True)
        return 1
    missing = missing_dependencies()
    if missing:
        print('[Setup] Missing or mismatched dependencies: ' + ', '.join(missing), flush=True)
        try:
            if not install_dependencies() or missing_dependencies():
                return 1
        except (OSError, subprocess.TimeoutExpired):
            print('[Setup] Installation could not finish. Your existing environment and reviews were preserved.', flush=True)
            return 1
    show_status()
    if args.check:
        print('Local app: ' + ('already running' if state == 'ours' else 'not running' if state == 'free' else 'port occupied'), flush=True)
        return 0
    if state == 'ours':
        print('ContextGuard is already running. Reusing ' + URL, flush=True)
        if os.getenv('CONTEXTGUARD_NO_BROWSER') != '1':
            webbrowser.open(URL)
        return 0
    print('Starting ' + URL + ' - keep this window open; press Ctrl+C to stop.', flush=True)
    threading.Thread(target=open_when_ready, daemon=True).start()
    try:
        return subprocess.call([sys.executable, str(ROOT / 'scripts/serve.py')])
    except KeyboardInterrupt:
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
