from pathlib import Path
import argparse
import os
import sys

import uvicorn

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8027)
    port = parser.parse_args().port
    if not 1024 <= port <= 65535:
        parser.error('Choose a local port between 1024 and 65535.')
    # OAuth callback codes and source IDs must not enter access logs.
    uvicorn.run('app.run:app', host='127.0.0.1', port=port, access_log=False, log_level='warning')
