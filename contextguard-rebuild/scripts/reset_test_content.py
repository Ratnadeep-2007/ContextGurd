"""Explicitly clear local review/test content while keeping identities and setup."""
import argparse
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT_KINDS = ('intake', 'review', 'decision', 'evidence', 'source_event', 'mapping', 'source')

def reset_content(database, *, server_stopped=False):
    connection = sqlite3.connect(database, timeout=10)
    try:
        connection.execute('BEGIN IMMEDIATE')
        jobs = [json.loads(row[0]) for row in connection.execute("SELECT body FROM records WHERE kind='intake'")]
        if not server_stopped and any(j['status'] in {'queued', 'routing', 'analyzing'} for j in jobs):
            raise RuntimeError('Processing is active. Stop the ContextGuard server before clearing test content.')
        placeholders = ','.join('?' for _ in CONTENT_KINDS)
        before = dict(connection.execute(f'SELECT kind,count(*) FROM records WHERE kind IN ({placeholders}) GROUP BY kind', CONTENT_KINDS))
        connection.execute(f'DELETE FROM records WHERE kind IN ({placeholders})', CONTENT_KINDS)
        connection.commit()
        return before
    finally:
        connection.close()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Delete captured sources, evidence, reviews, intakes and saved decisions')
    parser.add_argument('--server-stopped', action='store_true', help='Operator has verified the server is stopped; permit clearing interrupted jobs')
    args = parser.parse_args()
    if not args.apply:
        parser.error('Use --apply only when clearing test content is intended.')
    from dotenv import dotenv_values
    settings = dotenv_values(ROOT / '.env')
    database = Path(settings.get('CONTEXTGUARD_DB') or ROOT / 'data/contextguard.sqlite3')
    if not database.is_absolute():
        database = ROOT / database
    database = database.resolve()
    if not database.is_relative_to(ROOT) or not database.is_file():
        parser.error('Expected an existing database inside this rebuild workspace.')
    try:
        removed = reset_content(database, server_stopped=args.server_stopped)
    except RuntimeError as exc:
        parser.exit(1, str(exc) + '\n')
    print(json.dumps({'removed': removed, 'preserved': ['users', 'sessions', 'projects', 'roles', 'connection settings', 'sample files']}))

if __name__ == '__main__':
    main()
