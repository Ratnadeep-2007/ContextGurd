"""Private, on-demand Baileys process. No public bridge port or plaintext session keys."""
import base64
import json
import os
import queue
import re
import secrets
import shutil
import subprocess
import threading
from pathlib import Path

from .credentials import transform
from .service import Rejected, require

ROOT = Path(__file__).resolve().parents[1]


class WhatsApp:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.sessions = {}
        self.lock = threading.RLock()

    def available(self):
        return bool(shutil.which('node') and (self.root / 'connectors/whatsapp/node_modules/baileys/package.json').is_file()
                    and (self.root / 'connectors/whatsapp/node_modules/qrcode/package.json').is_file())

    def summary(self, workspace):
        result = {'configured': self.available(), 'status': 'Not paired' if self.available() else 'Setup required',
                  'runtime_available': self.available(), 'experimental': True, 'selected': [], 'message_count': 0,
                  'chats': [], 'qr_available': False}
        with self.lock:
            if workspace in self.sessions:
                try:
                    result.update(self.call(workspace, 'status'))
                except Rejected:
                    result['status'] = 'connection_failed'
        return result

    def _start(self, workspace):
        require(self.available(), 'Install the local WhatsApp runtime with setup-whatsapp.bat, then retry pairing.', 409)
        require(os.name == 'nt', 'Live session storage requires Windows credential protection.', 409)
        require(bool(re.fullmatch(r'[A-Za-z0-9_-]{1,100}', workspace)), 'Invalid workspace.', 403)
        directory = self.root / 'data/whatsapp' / workspace
        directory.mkdir(parents=True, exist_ok=True)
        # Explicit ACL: linked-device secrets belong to the current Windows user.
        try:
            identity = subprocess.run(['whoami'], capture_output=True, text=True, timeout=5, check=True).stdout.strip()
            acl = subprocess.run(['icacls', str(directory), '/inheritance:r', '/grant:r', identity + ':(OI)(CI)F'],
                                 capture_output=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            raise Rejected('Cannot protect the local session directory. Pairing was not started.', 409) from None
        require(acl.returncode == 0, 'Cannot protect the local session directory. Pairing was not started.', 409)
        key_file = directory / 'vault.dpapi'
        try:
            if key_file.exists():
                key = transform(key_file.read_text(), decrypt=True)
            else:
                key = base64.b64encode(secrets.token_bytes(32)).decode()
                key_file.write_text(transform(key))
        except (RuntimeError, ValueError, OSError):
            raise Rejected('Windows session protection failed. No plaintext credential was saved.', 409) from None
        process = subprocess.Popen([shutil.which('node'), str(self.root / 'connectors/whatsapp/bridge.mjs')],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding='utf-8',
            creationflags=subprocess.CREATE_NO_WINDOW)
        inbox = queue.Queue()
        def read():
            for line in process.stdout:
                try:
                    value = json.loads(line)
                    if isinstance(value, dict) and 'id' in value:
                        inbox.put(value)
                except ValueError:
                    pass  # Never echo child output; it could contain account data.
            inbox.put(None)
        threading.Thread(target=read, daemon=True).start()
        self.sessions[workspace] = {'process': process, 'inbox': inbox}
        try:
            self.call(workspace, 'initialize', {'key': key, 'file': str(directory / 'session.enc')})
        except Exception:
            self._close(workspace)
            raise

    def call(self, workspace, method, payload=None):
        with self.lock:
            if workspace not in self.sessions:
                require(method == 'connect', 'Pair WhatsApp first.', 409)
                self._start(workspace)
            session = self.sessions[workspace]
            process, inbox = session['process'], session['inbox']
            request_id = secrets.token_hex(8)
            try:
                process.stdin.write(json.dumps({'id': request_id, 'method': method, 'payload': payload or {}}) + '\n')
                process.stdin.flush()
                result = inbox.get(timeout=25)
                if result is None or result.get('id') != request_id:
                    raise OSError()
                require(not result.get('error'), result.get('error', 'WhatsApp operation failed.'), 409)
                return result['result']
            except (OSError, ValueError, queue.Empty):
                self._close(workspace)
                raise Rejected('WhatsApp reader stopped or timed out. Reconnect; manual import is available.', 409) from None

    def disconnect(self, workspace):
        with self.lock:
            try:
                if workspace in self.sessions:
                    self.call(workspace, 'disconnect')
            finally:
                self._close(workspace)
                # A stopped/offline reader can still be forgotten locally.
                directory = self.root / 'data/whatsapp' / workspace
                for name in ('session.enc', 'session.enc.tmp', 'vault.dpapi'):
                    (directory / name).unlink(missing_ok=True)
        return {'status': 'disconnected', 'note': 'Local session removed. Check Linked devices on your phone to revoke it there too.'}

    def _close(self, workspace):
        session = self.sessions.pop(workspace, None)
        if session:
            process = session['process']
            try:
                process.stdin.close()
                process.wait(timeout=3)
            except (OSError, subprocess.TimeoutExpired):
                process.kill()
                process.wait(timeout=3)
            process.stdout.close()

    def close(self):
        with self.lock:
            for workspace in list(self.sessions):
                self._close(workspace)
