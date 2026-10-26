"""Back up local records, remove verified mock projects, and seed one existing project."""
import argparse
import json
import os
import secrets
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.adapters import manual
from app.review import Reviews
from app.service import Rejected, now, require
from app.storage import Store

FIXTURE = 'contextguard-single-demo-v1'
PEOPLE = [('test.review.owner', 'Asha Patel', 'reviewer', 'Requirements and cost'),
          ('test.product.owner', 'Mira Rao', 'decision_owner', 'Pilot date and scope'),
          ('test.engineer', 'Dev Shah', 'reviewer', 'Dependencies, versions and performance'),
          ('test.security.owner', 'Leena Nair', 'decision_owner', 'Security approval')]


def consolidate(service, owner, keep_id):
    """Caller must back up the DB before invoking. Never delete non-fictional records."""
    store = service.store
    require(owner['role'] == 'owner', 'A workspace admin is required.', 403)
    with store.transaction():
        keep = service.project(owner, keep_id)
        projects = store.all('project', owner['workspace'])
        remove = [p for p in projects if p['id'] != keep_id]
        ids = {p['id'] for p in remove}
        for project in remove:
            require('fictional' in project['name'].casefold() or project.get('test_fixture'),
                    'Another non-demo project exists. It was preserved; no cleanup was performed.')
        evidence = store.all('evidence', owner['workspace'])
        reviews = store.all('review', owner['workspace'])
        decisions = store.all('decision', owner['workspace'])
        require(all(e.get('test_mode') for e in evidence if e.get('project_id') in ids) and
                all(r.get('test_mode') for r in reviews if r['project_id'] in ids) and
                not any(d['project_id'] in ids for d in decisions),
                'A candidate project contains non-demo evidence or confirmed decisions. Nothing was removed.')
        jobs = store.all('intake', owner['workspace'])
        require(not any(j['status'] in {'queued', 'routing', 'analyzing'} for j in jobs),
                'Wait for active processing to finish before cleaning demo data.')
        affected_jobs = [j for j in jobs if ids.intersection(j['project_ids'])]
        require(all(j.get('test_mode') for j in affected_jobs), 'A real input references a demo project. Nothing was removed.')
        source_ids = {e['source_id'] for e in evidence if e.get('project_id') in ids}
        source_ids.update(sid for j in affected_jobs for sid in j['source_ids'])
        require(not any(e.get('project_id') not in ids and e['source_id'] in source_ids for e in evidence),
                'A demo source is shared with retained evidence. Nothing was removed.')
        review_ids = {r['id'] for r in reviews if r['project_id'] in ids}
        deleted = {}
        def drop(kind, records):
            for row in records:
                store.db.execute('DELETE FROM records WHERE kind=? AND id=? AND workspace=?',
                                 (kind, row['id'], owner['workspace']))
            deleted[kind] = len(records)
        drop('review', [r for r in reviews if r['id'] in review_ids])
        drop('evidence', [e for e in evidence if e.get('project_id') in ids])
        drop('source_event', [e for e in store.all('source_event', owner['workspace']) if e['source_id'] in source_ids])
        drop('source', [s for s in store.all('source', owner['workspace']) if s['id'] in source_ids])
        drop('mapping', [m for m in store.all('mapping', owner['workspace']) if m['project_id'] in ids or m['source_id'] in source_ids])
        drop('intake', affected_jobs)
        drop('project', remove)
        drop('test_fixture', [f for f in store.all('test_fixture', owner['workspace'])
                              if f['id'].startswith('contextguard-assignment-v1')])
        accounts = []
        for username, name, role, topic in PEOPLE:
            user = next((u for u in store.all('user', owner['workspace']) if u['username'] == username), None)
            password = None
            if not user:
                password = secrets.token_urlsafe(20)
                created = service.create_user(username, password, owner)
                user = store.get('user', created['id'])
            require(user.get('test_fixture') or password, 'An existing test name belongs to a non-demo user.')
            user.update(display_name=name, test_fixture=FIXTURE, responsibility_label=topic)
            store.put('user', user)
            service.member(owner, keep_id, user['id'], role)
            accounts.append({**service.public_user(user), 'password': password, 'project_role': role,
                             'responsibility': topic})
        owner_row = store.get('user', owner['id'])
        owner_row['display_name'] = owner['username'].capitalize()
        store.put('user', owner_row)
        keep = service.project(owner, keep_id)
        keep.update(demo_fixture=FIXTURE)
        if not keep.get('description'):
            keep['description'] = 'Synora fictional pilot: scope, dates, security approval and integration dependencies. All sample documents are fictional.'
        if not keep.get('goal'):
            keep['goal'] = 'Can the fictional Synora v2 pilot proceed?'
        keep['responsibilities'] = {'date disagreement': accounts[1]['id'], 'security': accounts[3]['id'],
            'service cost': accounts[0]['id'], 'credentials': accounts[2]['id'],
            'version': accounts[2]['id'], 'performance': accounts[2]['id']}
        store.put('project', keep)
        previous = next((r for r in reviews if r['project_id'] == keep_id and r.get('demo_fixture') == FIXTURE), None)
        if previous:
            return {'project': keep, 'accounts': accounts, 'review': previous, 'deleted': deleted}
        # Existing retained user data is never replaced by this demo operation.
        require(not any(e.get('project_id') == keep_id for e in evidence) and not any(r['project_id'] == keep_id for r in reviews),
                'The retained project has existing content. Nothing was changed; use a dedicated empty project.')
        sources = []
        for path in sorted((ROOT / 'samples').glob('*.md')):
            text = path.read_text(encoding='utf-8').replace('Orchid', 'Synora')
            source = service.create_source(owner, 'manual', FIXTURE + ':' + keep_id + ':' + path.name,
                'Fictional Synora · ' + path.name, [a['id'] for a in accounts])
            passages = manual(path.name, text.encode('utf-8'))
            service.ingest(owner, {'source_id': source['id'], 'project_id': keep_id, 'consent': True, 'test_mode': True,
                'passages': [p.model_dump(mode='json') for p in passages], 'original': {'fictional_demo': True, 'filename': path.name, 'text': text}})
            sources.append(source['id'])
        review = service.analyze(owner, keep_id, keep['goal'], sources, test_mode=True)
        require(len(review['findings']) == 6, 'Demo verification failed; the transaction was rolled back.')
        review['demo_fixture'] = FIXTURE
        store.put('review', review)
        for finding in review['findings']:
            service.assign(owner, review['id'], finding['id'], finding['suggested_assignee_id'])
        keep['demo_source_ids'] = sources
        store.put('project', keep)
        return {'project': keep, 'accounts': accounts, 'review': service.get_review(owner, review['id']), 'deleted': deleted}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--project', default='synora')
    args = parser.parse_args()
    require(args.apply, 'Use --apply to make the explicitly requested demo cleanup.')
    from dotenv import load_dotenv
    load_dotenv(ROOT / '.env', override=False)
    path = Path(os.getenv('CONTEXTGUARD_DB', 'data/contextguard.sqlite3'))
    if not path.is_absolute():
        path = ROOT / path
    require(path.is_file(), 'Application database not found.')
    store = Store(path)
    try:
        owners = [u for u in store.all('user') if u['username'].casefold() == 'ratnadeep' and u['role'] == 'owner']
        require(len(owners) == 1, 'Expected the existing Ratnadeep admin; no accounts were changed.')
        owner = owners[0]
        matches = [p for p in store.all('project', owner['workspace']) if p['name'].casefold() == args.project.casefold()]
        require(len(matches) == 1, 'Select one existing project to retain.')
        folder = ROOT / 'artifacts' / ('demo-backup-' + uuid4().hex)
        folder.mkdir(parents=True)
        import sqlite3
        with sqlite3.connect(folder / 'contextguard.sqlite3') as backup:
            store.db.backup(backup)
        credentials = ROOT / 'artifacts/test-users/credentials.json'
        previous = json.loads(credentials.read_text(encoding='utf-8')) if credentials.exists() else {'accounts': []}
        (folder / 'credentials.json').write_text(json.dumps(previous, indent=2), encoding='utf-8')
        with store.transaction():
            result = consolidate(Reviews(store), owner, matches[0]['id'])
            for account in result['accounts']:
                old = next((u for u in previous['accounts'] if u['id'] == account['id']), {})
                account['password'] = account['password'] or old.get('password')
            project, review = result['project'], result['review']
            manifest = {'created': now(), 'accounts': result['accounts'], 'projects': [{
                'id': project['id'], 'name': project['name'], 'review_id': review['id'],
                'roles': {a['username']: a['project_role'] for a in result['accounts']},
                'assignments': [{'finding_id': f['id'], 'title': f['title'], 'assignee': next(
                    a['username'] for a in result['accounts'] if a['id'] == f['assignee_id'])} for f in review['findings']]}]}
            credentials.parent.mkdir(parents=True, exist_ok=True)
            credentials.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        print(json.dumps({'project': project['name'], 'projects_remaining': 1, 'findings': len(review['findings']),
                          'mock_members': len(result['accounts']), 'deleted': result['deleted'], 'private_backup': str(folder)}))
    finally:
        store.db.close()


if __name__ == '__main__':
    try:
        main()
    except Rejected as exc:
        raise SystemExit(exc.message)
