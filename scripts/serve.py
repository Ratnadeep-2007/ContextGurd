from pathlib import Path
import os
import sys

import uvicorn

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

if __name__ == '__main__':
    # OAuth callback codes and source IDs must not enter access logs.
    uvicorn.run('app.run:app', host='127.0.0.1', port=8027, access_log=False, log_level='warning')
