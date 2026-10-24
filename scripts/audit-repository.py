"""Read-only repository/history audit. Reports paths and reasons, never key values."""
import io
import json
import re
import subprocess
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def audit():
    secrets = {key: value.encode() for key, value in dotenv_values(ROOT / '.env').items() if value and len(value) >= 12 and re.search(r'(KEY|TOKEN|PASSWORD|SECRET)$', key)}
    findings = []
    forbidden = re.compile(r'(^|/)(\.env(?:\..*)?|learner-profile\.md|id_rsa|[^/]+\.(?:sqlite3?|db|pem|p12))$|(^|/)(?:node_modules|\.venv|__pycache__|data|artifacts)/')
    token = re.compile(rb'(?:gsk_[A-Za-z0-9]{20,}|nvapi-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-(?:proj-)?[A-Za-z0-9_-]{24,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')
    revisions = git('rev-list', '--all').decode().splitlines()
    checked_blobs = set()
    def inspect_content(path, content, revision):
        if path == '.env.example':
            values = dotenv_values(stream=io.StringIO(content.decode('utf-8')))
            for name, value in values.items():
                if re.search(r'(KEY|TOKEN|PASSWORD|SECRET)$', name) and value:
                    findings.append({'revision': revision, 'path': path, 'reason': 'Nonempty credential field in example: ' + name})
        for name, secret in secrets.items():
            if secret in content:
                findings.append({'revision': revision, 'path': path, 'reason': 'Exact configured credential match: ' + name})
        if token.search(content):
            findings.append({'revision': revision, 'path': path, 'reason': 'Credential/private-key pattern requires review'})
    for revision in revisions:
        rows = git('ls-tree', '-rz', '--full-tree', revision).split(b'\0')
        for row in rows:
            if not row:
                continue
            metadata, path_raw = row.split(b'\t', 1)
            _, kind, blob = metadata.decode().split()
            path = path_raw.decode('utf-8', 'replace')
            if path != '.env.example' and forbidden.search(path):
                findings.append({'revision': revision, 'path': path, 'reason': 'Private/generated file tracked'})
            if kind != 'blob' or blob in checked_blobs:
                continue
            checked_blobs.add(blob)
            content = git('cat-file', 'blob', blob)
            inspect_content(path, content, revision)
    for row in git('ls-files', '--stage', '-z').split(b'\0'):
        if not row:
            continue
        metadata, path_raw = row.split(b'\t', 1)
        _, blob, _ = metadata.decode().split()
        path = path_raw.decode('utf-8', 'replace')
        if path != '.env.example' and forbidden.search(path):
            findings.append({'revision': 'INDEX', 'path': path, 'reason': 'Private/generated file staged or tracked'})
        if blob not in checked_blobs and set(blob) != {'0'}:
            inspect_content(path, git('cat-file', 'blob', blob), 'INDEX')
    worktree = set(git('ls-files', '-co', '--exclude-standard', '-z').decode().split('\0')) - {''}
    for path in sorted(worktree):
        file = ROOT / path
        if not file.is_file():
            continue
        if path != '.env.example' and forbidden.search(path):
            findings.append({'revision': 'WORKTREE', 'path': path, 'reason': 'Private/generated file included in publishable files'})
        inspect_content(path, file.read_bytes(), 'WORKTREE')
    built_files = [file for file in (ROOT / 'frontend' / 'dist').rglob('*') if file.is_file() and file.suffix in {'.js', '.css', '.html', '.json', '.svg'}]
    for file in built_files:
        inspect_content(str(file.relative_to(ROOT)).replace('\\', '/'), file.read_bytes(), 'BUILD')
    tracked = git('ls-files', '-z').decode().split('\0')
    required = ['LICENSE', 'README.md', '.gitignore', '.env.example', 'devpost/scope.md', 'devpost/prd.md', 'devpost/spec.md']
    result = {'head': git('rev-parse', 'HEAD').decode().strip(), 'commit_count': len(revisions), 'unique_history_blobs_checked': len(checked_blobs), 'worktree_files_checked': len(worktree), 'built_files_checked': len(built_files), 'required_files_present': {path: path in tracked for path in required}, 'findings': findings, 'method': 'Reachable git history, index, nonignored worktree files and text build assets checked against configured credential values and common token patterns; private/generated paths and nonempty example key fields checked. This is not a proof that every possible secret or licensing issue is absent.'}
    destination = ROOT / 'artifacts' / 'release-verification' / 'repository-audit.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 1 if findings or not all(result['required_files_present'].values()) else 0


if __name__ == '__main__':
    raise SystemExit(audit())
