"""Run tests in a new workspace-local temp folder, without touching user records."""
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
artifacts = ROOT / 'artifacts'
artifacts.mkdir(exist_ok=True)
raise SystemExit(subprocess.call([sys.executable, '-m', 'pytest', '--basetemp', str(artifacts / ('pytest-' + uuid4().hex)), *sys.argv[1:]], cwd=ROOT))
