"""Local, fictional credential-protection round trip. Never opens a socket or prints secrets."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.credentials import transform

if __name__ == '__main__':
    try:
        value = 'fictional-whatsapp-protection-probe'
        if transform(transform(value), decrypt=True) != value:
            raise RuntimeError()
    except (RuntimeError, OSError, ValueError):
        print('Windows session protection is unavailable. Run from your normal Windows user session; pairing remains blocked safely.')
        raise SystemExit(1)
    print('Windows current-user session protection verified. No WhatsApp account was contacted.')
