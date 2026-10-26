import json
import sqlite3
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from threading import RLock


class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = RLock()
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('CREATE TABLE IF NOT EXISTS records(kind TEXT,id TEXT PRIMARY KEY,workspace TEXT,body TEXT NOT NULL)')
        self.db.execute('CREATE INDEX IF NOT EXISTS workspace_kind ON records(workspace,kind)')
        self.db.commit()

    @contextmanager
    def transaction(self):
        with self.lock:
            nested = self.db.in_transaction
            if not nested:
                self.db.execute('BEGIN IMMEDIATE')
            try:
                yield
                if not nested:
                    self.db.commit()
            except BaseException:
                if not nested:
                    self.db.rollback()
                raise

    def put(self, kind, obj):
        with self.transaction():
            self.db.execute('INSERT INTO records VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body',
                            (kind, obj['id'], obj.get('workspace', ''), json.dumps(obj)))
        return obj

    def get(self, kind, key):
        with self.lock:
            row = self.db.execute('SELECT body FROM records WHERE kind=? AND id=?', (kind, key)).fetchone()
            return json.loads(row[0]) if row else None

    def all(self, kind, workspace=None):
        with self.lock:
            rows = self.db.execute('SELECT body FROM records WHERE kind=?' + (' AND workspace=?' if workspace else ''),
                                   (kind, workspace) if workspace else (kind,)).fetchall()
            return [json.loads(r[0]) for r in rows]


def atomic(method):
    @wraps(method)
    def call(self, *args, **kwargs):
        with self.store.transaction():
            return method(self, *args, **kwargs)
    return call
