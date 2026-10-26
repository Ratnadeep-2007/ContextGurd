"""Read-only publishable-file/history scan. Never print credential values."""
import io
import json
import os
import re
import subprocess
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, stderr=subprocess.DEVNULL)


def main():
    secret_values = list(dotenv_values(ROOT / '.env').items()) + list(os.environ.items())
    secrets = [v.encode() for k, v in secret_values if v and len(v) >= 12 and re.search(r'(API_KEY|TOKEN|PASSWORD|SECRET)$', k)]
    findings = []
    pattern = re.compile(rb'gsk_[A-Za-z0-9]{20,}|nvapi-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')
    def inspect(path, content, stage):
        if pattern.search(content) or any(value in content for value in secrets):
            findings.append({'path': path, 'stage': stage, 'reason': 'Credential pattern or exact configured value; inspect privately'})
        if path == '.env.example':
            values = dotenv_values(stream=io.StringIO(content.decode('utf-8')))
            if any(value for name, value in values.items() if re.search(r'(KEY|TOKEN|PASSWORD|SECRET)$', name)):
                findings.append({'path': path, 'stage': stage, 'reason': 'Example has a nonempty credential field'})
    private = re.compile(r'(^|/)(?:\.env(?:\..*)?|learner-profile\.md|[^/]+\.(?:db|sqlite3?|pem))$|(^|/)(?:\.venv|node_modules|artifacts|data|\.agents)/')
    files = set(git('ls-files', '-co', '--exclude-standard', '-z').decode().split('\0')) - {''}
    for name in sorted(files):
        file = ROOT / name
        if file.is_file():
            if name != '.env.example' and private.search(name):
                findings.append({'path': name, 'stage': 'worktree', 'reason': 'Private/generated file included'})
            inspect(name, file.read_bytes(), 'worktree')
    blobs = set()
    for revision in git('rev-list', '--all').decode().splitlines():
        for row in git('ls-tree', '-rz', revision).split(b'\0'):
            if not row:
                continue
            metadata, name = row.split(b'\t', 1)
            _, kind, sha = metadata.decode().split()
            name = name.decode()
            if name != '.env.example' and private.search(name):
                findings.append({'path': name, 'stage': revision, 'reason': 'Private/generated path in history'})
            if kind == 'blob' and sha not in blobs:
                inspect(name, git('cat-file', 'blob', sha), revision)
                blobs.add(sha)
    result = {'publishable_files': len(files), 'history_blobs': len(blobs), 'findings': findings,
              'limitation': 'Pattern/exact-value scan, not proof that every possible secret or licensing issue is absent.'}
    out = ROOT / 'artifacts/repository-audit.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    return bool(findings)


if __name__ == '__main__':
    raise SystemExit(main())
