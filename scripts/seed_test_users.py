"""Create isolated, fictional assignment fixtures. No model or source connection is used."""
import argparse
import json
import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.adapters import manual
from app.review import Reviews
from app.service import Rejected, now, require
from app.storage import Store

FIXTURE = 'contextguard-assignment-v1'
NAMES = ('test.review.owner', 'test.product.owner', 'test.engineer', 'test.security.owner')
ROLES = {
    'Orchid': ('owner', 'decision_owner', 'reviewer', 'decision_owner'),
    'Cedar': ('owner', None, 'decision_owner', 'decision_owner'),
}


def seed(service, owner):
    """Return a private manifest. Transactional and idempotent; never reset accounts."""
    require(owner['role'] == 'owner', 'A workspace owner is required.', 403)
    store = service.store
    with store.transaction():
        saved = store.get('test_fixture', FIXTURE + '-' + owner['workspace'])
        if saved:
            return saved, False
        existing = {u['username'].casefold() for u in store.all('user')}
        require(not existing.intersection(NAMES), 'A test username already exists; no accounts were changed.')
        accounts = []
        for name in NAMES:
            password = secrets.token_urlsafe(20)
            user = service.create_user(name, password, owner)
            row = store.get('user', user['id'])
            row['test_fixture'] = FIXTURE
            store.put('user', row)
            accounts.append({**user, 'password': password})
        review_owner = accounts[0]
        projects = []
        for title, roles in ROLES.items():
            project = service.create_project(owner, 'TEST - ' + title + ' (fictional)')
            project['test_fixture'] = FIXTURE
            store.put('project', project)
            for user, role in zip(accounts, roles):
                if role:
                    service.member(owner, project['id'], user['id'], role)
            product = accounts[1] if title == 'Orchid' else accounts[2]
            for topic, user in [('date disagreement', product), ('security', accounts[3]),
                                ('service', accounts[2]), ('credentials', accounts[2]),
                                ('version', accounts[2]), ('performance', accounts[2])]:
                service.responsibility(owner, project['id'], topic, user['id'])
            grants = [owner['id']] + [u['id'] for u, role in zip(accounts, roles) if role]
            sources = []
            for path in sorted((ROOT / 'samples').glob('*.md')):
                # Each project gets distinct, explicitly fictional sources; no cross-project routing.
                content = path.read_text(encoding='utf-8').replace('Orchid', title)
                source = service.create_source(owner, 'manual', f'{FIXTURE}/{project["id"]}/{path.name}',
                                               f'TEST {title}: {path.name}', grants)
                passages = manual(path.name, content.encode('utf-8'))
                service.ingest(owner, {'source_id': source['id'], 'project_id': project['id'],
                                      'consent': True, 'test_mode': True,
                                      'passages': passages, 'original': {'fixture': FIXTURE}})
                sources.append(source['id'])
            review = service.analyze(review_owner, project['id'],
                                     f'Can the fictional {title} v2 pilot proceed?', sources, test_mode=True)
            require(review['status'] == 'complete' and len(review['findings']) == 6,
                    'Expected six fictional findings; nothing was saved.')
            assignments = []
            for finding in review['findings']:
                uid = finding['suggested_assignee_id']
                require(uid is not None, 'A fictional responsibility mapping is missing.')
                service.assign(review_owner, review['id'], finding['id'], uid)
                assignments.append({'finding_id': finding['id'], 'title': finding['title'],
                                    'assignee': next(u['username'] for u in accounts if u['id'] == uid)})
            projects.append({'id': project['id'], 'name': project['name'], 'review_id': review['id'],
                             'roles': {u['username']: role for u, role in zip(accounts, roles) if role},
                             'assignments': assignments})
        result = {'id': FIXTURE + '-' + owner['workspace'], 'workspace': owner['workspace'],
                  'created': now(), 'accounts': accounts, 'projects': projects,
                  'note': 'Fictional test mode. Findings remain open; no decisions or messages were created.'}
        # Do not persist plaintext credentials in the app database.
        record = {**result, 'accounts': [{k: v for k, v in u.items() if k != 'password'} for u in accounts]}
        store.put('test_fixture', record)
        return result, True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--create', action='store_true', help='Explicitly create the local test fixtures')
    parser.add_argument('--owner', help='Existing workspace owner username')
    args = parser.parse_args()
    if not args.create:
        parser.error('Pass --create to create local test accounts and projects.')
    from dotenv import load_dotenv
    load_dotenv(ROOT / '.env', override=False)
    path = Path(os.getenv('CONTEXTGUARD_DB', str(ROOT / 'data/contextguard.sqlite3')))
    if not path.is_absolute():
        path = ROOT / path
    require(path.is_file(), 'The local application database does not exist. Run setup first.')
    store = Store(path)
    try:
        owners = [u for u in store.all('user') if u['role'] == 'owner'
                  and (not args.owner or u['username'].casefold() == args.owner.casefold())]
        require(len(owners) == 1, 'Select the existing workspace owner with --owner.')
        output = ROOT / 'artifacts/test-users/credentials.json'
        # Reserve the private output before mutation, so a failed file open cannot lose new credentials.
        output.parent.mkdir(parents=True, exist_ok=True)
        marker = store.get('test_fixture', FIXTURE + '-' + owners[0]['workspace'])
        require(not marker or output.is_file(), 'Fixtures already exist; credentials were not reset.')
        mode = 'r+' if marker else 'x'
        with output.open(mode, encoding='utf-8') as private:
            with store.transaction():
                result, created = seed(Reviews(store), owners[0])
                if created:
                    private.write(json.dumps(result, indent=2) + '\n')
                    private.flush()
                    os.fsync(private.fileno())
        print(json.dumps({'created': created, 'users': len(result['accounts']),
                          'projects': len(result['projects']), 'private_credentials': str(output)}))
    finally:
        store.db.close()


if __name__ == '__main__':
    try:
        main()
    except Rejected as exc:
        raise SystemExit(exc.message)
