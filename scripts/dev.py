"""Run the API and Vite with one command. Ctrl+C stops both children."""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    node = shutil.which("node")
    vite = ROOT / "frontend/node_modules/vite/bin/vite.js"
    if not node or not vite.exists():
        raise SystemExit("Install Node.js and run npm install in frontend first.")
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    processes = []
    try:
        processes.append(subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8017"], cwd=ROOT, creationflags=flags))
        processes.append(subprocess.Popen([node, str(vite), "--host", "127.0.0.1"], cwd=ROOT / "frontend", creationflags=flags))
        print("ContextGuard: http://localhost:5173 · API: http://localhost:8017/api/health", flush=True)
        while all(p.poll() is None for p in processes):
            time.sleep(.5)
    except KeyboardInterrupt:
        pass
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
