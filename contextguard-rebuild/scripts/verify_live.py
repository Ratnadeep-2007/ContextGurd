"""Explicit live checks. Fictional model input; no hidden source calls or secret output."""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sys
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import httpx
from dotenv import load_dotenv

from app.adapters import AdapterFailure, Slack, Vexa, manual
from app.credentials import transform
from app.providers import ProviderFailure, Providers
from app.review import Reviews
from app.service import Rejected
from app.storage import Store

KEYS = ('MODEL_API_KEY', 'GROQ_API_KEY', 'NVIDIA_API_KEY')
PROVIDERS = {'muse': ('Muse Wonder', 'MODEL_API_KEY'), 'groq': ('Groq', 'GROQ_API_KEY'), 'nvidia': ('NVIDIA', 'NVIDIA_API_KEY')}


@contextmanager
def only_provider(key):
    saved = {name: os.environ.get(name) for name in KEYS}
    try:
        for name in KEYS:
            if name != key:
                os.environ[name] = ''
        yield
    finally:
        for name, value in saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


class FailPrimaryOnce(httpx.BaseTransport):
    """A labeled controlled-primary-failure test with real fallback HTTP, never a real outage claim."""
    def __init__(self):
        self.delegate = None
        self.first = True

    def handle_request(self, request):
        if self.first:
            self.first = False
            raise httpx.ConnectError('Controlled test: primary request not sent.', request=request)
        if self.delegate is None:
            self.delegate = httpx.HTTPTransport(retries=0)
        return self.delegate.handle_request(request)

    def close(self):
        if self.delegate is not None:
            self.delegate.close()
            self.delegate = None


def project_for_test(service, operator, name):
    project = service.create_project(operator, name)
    sources = []
    for file in sorted((ROOT / 'samples').glob('*.md')):
        source = service.create_source(operator, 'manual', file.name, 'Fictional ' + file.name)
        paragraphs = manual(file.name, file.read_bytes())
        service.ingest(operator, {'source_id': source['id'], 'project_id': project['id'], 'consent': True,
                                 'test_mode': True, 'passages': [p.model_dump(mode='json') for p in paragraphs],
                                 'original': {'filename': file.name, 'text': file.read_text(encoding='utf-8')}})
        sources.append(source['id'])
    return project, sources


def summarize(service, operator, review, directory, filename):
    failures = [part for item in review['failures'] for part in item.split('; ') if not part.endswith(': not configured')]
    if review['status'] == 'failed' and not failures:
        failures = ['Required endpoint, model or key is incomplete for this isolated provider check.']
    summary = {'analysis_status': review['status'], 'provider_used': review['provider'],
               'findings': len(review['findings']), 'failures': failures,
               'human_semantic_review_required': True, 'mode': 'Real model, fictional source documents'}
    if review['status'] == 'complete' and not review['failures']:
        # Analysis.verified has already checked every displayed quote/decision reference.
        summary['status'] = 'live_schema_citations_and_report_verified'
        summary['potential_conflicts'] = sum(f['kind'] == 'potential_conflict' for f in review['findings'])
        (directory / filename).write_text(service.brief(operator, review['id']), encoding='utf-8')
    else:
        summary['status'] = 'not_verified'
    return summary


def check_models(service, operator, project, sources, directory, selected):
    results = []
    for code in (PROVIDERS if selected == 'all' else [selected]):
        name, key = PROVIDERS[code]
        if not os.getenv(key):
            results.append({'provider': name, 'status': 'not_configured'})
            continue
        with only_provider(key):
            service.providers = Providers()
            review = service.analyze(operator, project['id'], 'Can the fictional Orchid v2 pilot proceed? Inspect conflicting pilot dates, approvals, assumptions and dependencies; do not choose the truth.', sources, consent=True)
        result = {'provider': name, **summarize(service, operator, review, directory, code + '-report.md')}
        results.append(result)
        print(name + ': ' + result['status'], flush=True)
        for failure in result['failures']:
            print('  ' + failure, flush=True)
    return results


def check_fallback(service, operator, project, sources, directory, individual):
    fallback_worked = any(r['provider'] in {'Groq', 'NVIDIA'} and r['status'] == 'live_schema_citations_and_report_verified' for r in individual)
    if not fallback_worked or not all(os.getenv(k) for k in ('MODEL_API_KEY', 'MODEL_BASE_URL', 'MODEL_NAME')):
        return {'status': 'not_verified', 'reason': 'Needs a configured primary and a successful real fallback response first.'}
    # Observed live: one analysis consumes roughly half of Groq's 8,000-token/minute
    # window, so a second analysis in the same minute is quota-rejected. Pace the
    # fallback scenario instead of misreporting a quota rejection as a routing failure.
    print('Waiting 65s for the fallback provider quota window before the controlled-failure scenario...', flush=True)
    time.sleep(65)
    service.providers = Providers(FailPrimaryOnce())
    review = service.analyze(operator, project['id'], 'Check consistency of the fictional internal pilot plan.', sources, consent=True)
    return {**summarize(service, operator, review, directory, 'fallback-report.md'),
            'mode': 'Controlled local primary failure; actual external fallback request, not a naturally observed outage'}


def check_sources(service, operator, args):
    results = []
    # Selecting names alone never confers meeting/chat consent or a project route.
    if not args.sources:
        return [{'source': 'Vexa/Slack', 'status': 'not_requested', 'reason': 'Use --sources --source-consent --project with a selected authorized fictional test source.'}]
    if not args.source_consent or not args.project:
        return [{'source': 'Vexa/Slack', 'status': 'needs_selection_and_consent',
                 'reason': 'Supply --source-consent and an explicit --project before any real source request.'}]
    project = service.create_project(operator, args.project)
    for kind in ('vexa', 'slack'):
        if kind == 'vexa':
            missing = ([] if (os.getenv('VEXA_API_KEY') or os.getenv('VEXA_BOT_KEY')) else ['VEXA_BOT_KEY (or combined VEXA_API_KEY)'])
            missing += ([] if (os.getenv('VEXA_API_KEY') or os.getenv('VEXA_TX_KEY')) else ['VEXA_TX_KEY (or combined VEXA_API_KEY)'])
            missing += [key for key in ('VEXA_TEST_PLATFORM', 'VEXA_TEST_MEETING_ID') if not os.getenv(key)]
        else:
            missing = [key for key in ('SLACK_BOT_TOKEN', 'SLACK_TEAM_ID', 'SLACK_TEST_CHANNEL_ID') if not os.getenv(key)]
        if missing:
            results.append({'source': kind, 'status': 'not_configured', 'missing_setting_names': missing})
            continue
        try:
            if kind == 'vexa':
                client = Vexa(os.getenv('VEXA_BASE_URL', 'https://api.cloud.vexa.ai'), os.getenv('VEXA_API_KEY'),
                              bot_key=os.getenv('VEXA_BOT_KEY'), tx_key=os.getenv('VEXA_TX_KEY'))
                platform, meeting = os.environ['VEXA_TEST_PLATFORM'], os.environ['VEXA_TEST_MEETING_ID']
                if args.join_vexa:
                    if not args.participants_informed:
                        results.append({'source': kind, 'status': 'participant_consent_required'}); continue
                    client.join(platform, meeting, True, os.getenv('VEXA_TEST_PASSCODE'))
                passages, original = client.fetch(platform, meeting)
                container = platform + ':' + meeting
            else:
                team, channel = os.environ['SLACK_TEAM_ID'], os.environ['SLACK_TEST_CHANNEL_ID']
                passages, original = Slack(os.environ['SLACK_BOT_TOKEN'], team).fetch(channel, os.getenv('SLACK_TEST_THREAD_TS'))
                container = team + ':' + channel
            if not passages:
                raise AdapterFailure('No selected source passages returned; no content was invented.')
            source = service.create_source(operator, kind, container, 'Authorized live test source')
            rows = service.ingest(operator, {'source_id': source['id'], 'project_id': project['id'], 'consent': True,
                                            'passages': [p.model_dump(mode='json') for p in passages], 'original': original})
            results.append({'source': kind, 'status': 'real_source_to_routed_evidence_verified', 'passages': len(rows),
                            'complete': all(p.extraction == 'complete' for p in passages),
                            'limitation': 'No real source content sent to a model. Goal-report and browser/account acceptance still require explicit in-app review.'})
        except (AdapterFailure, Rejected, ValueError) as exc:
            reason = str(exc) if isinstance(exc, (AdapterFailure, Rejected)) else 'Source payload validation failed.'
            results.append({'source': kind, 'status': 'not_verified', 'reason': reason})
    return results


def whatsapp_readiness():
    # Never produce a QR or fall back to plaintext credentials when protection is unavailable.
    try:
        protected = transform('fictional-credential-probe')
        storage = transform(protected, decrypt=True) == 'fictional-credential-probe'
    except RuntimeError:
        storage = False
    return {'source': 'WhatsApp/Baileys', 'status': 'not_connected', 'protected_storage_available': storage,
            'reason': 'Experimental pairing is implemented; dependency installation and a real account QR scan remain unverified. Run setup-whatsapp.bat, then use Sources. This readiness probe never starts a socket or produces a QR.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Authorize real model requests containing the bundled fictional documents')
    parser.add_argument('--models', choices=['all', *PROVIDERS], default='all')
    parser.add_argument('--fallback', action='store_true', help='After successful fallback access, test controlled-primary-failure routing to a real fallback')
    parser.add_argument('--sources', action='store_true', help='Read explicitly configured selected real test sources')
    parser.add_argument('--source-consent', action='store_true')
    parser.add_argument('--project', help='Explicit project name for isolated selected-source routing')
    parser.add_argument('--join-vexa', action='store_true', help='Explicitly request a meeting bot; no hidden automatic join')
    parser.add_argument('--participants-informed', action='store_true')
    args = parser.parse_args(argv)
    if not args.live and not args.sources:
        parser.error('Use --live for fictional model checks or --sources with explicit selection/consent.')
    if args.fallback and not args.live:
        parser.error('--fallback requires --live.')
    load_dotenv(ROOT / '.env', override=False)
    directory = ROOT / 'artifacts/live-checks' / uuid4().hex
    directory.mkdir(parents=True)
    service = Reviews(Store(directory / 'verification.sqlite3'))
    operator = service.create_user('Automated fictional verification operator', uuid4().hex)
    report = {'mode': 'Isolated verification, not normal project memory or final human approval', 'models': [], 'sources': []}
    try:
        if args.live:
            project, sources = project_for_test(service, operator, 'Fictional Orchid model verification')
            report['models'] = check_models(service, operator, project, sources, directory, args.models)
            if args.fallback:
                report['fallback'] = check_fallback(service, operator, project, sources, directory, report['models'])
        report['sources'] = check_sources(service, operator, args)
        report['whatsapp'] = whatsapp_readiness()
        output = directory / 'results.json'
        output.write_text(json.dumps(report, indent=2), encoding='utf-8')
        print('Results saved locally: ' + str(output.relative_to(ROOT)), flush=True)
        print('Vexa/Slack/WhatsApp are not declared integrated by a configuration or mock check.', flush=True)
        passed = True
        if args.live:
            passed = all(r['status'] == 'live_schema_citations_and_report_verified' for r in report['models'])
            if args.fallback:
                passed = passed and report['fallback']['status'] == 'live_schema_citations_and_report_verified'
        if args.sources:
            passed = passed and all(r['status'] == 'real_source_to_routed_evidence_verified' for r in report['sources'])
        return 0 if passed else 2
    finally:
        service.store.db.close()


if __name__ == '__main__':
    raise SystemExit(main())
