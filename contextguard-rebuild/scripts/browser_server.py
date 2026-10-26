"""Start an isolated fictional browser-test server. Never contacts model providers."""
import argparse
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    import uvicorn
    from app.api import create_app
    from app.providers import ProviderFailure, Providers

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8037)
    parser.add_argument('--progress-fixture', action='store_true', help='Slow fictional responses for progress UI checks; no external calls')
    args = parser.parse_args()
    port = args.port
    if not 1024 <= port <= 65535:
        parser.error('Use a local port between 1024 and 65535.')

    class OfflineProviders(Providers):
        def request(self, *args, **kwargs):
            raise ProviderFailure('Controlled browser test: model unavailable. Input retained.')

    class ProgressProviders:
        def classify(self, units, projects, context):
            import time
            from app.contracts import ConversationRoutes
            time.sleep(.35)
            if any('FAIL_PROGRESS_CHECK' in unit['text'] for unit in units):
                raise ProviderFailure('Controlled progress check: model unavailable. Input retained.')
            return ConversationRoutes(routes=[{'unit_id': unit['id'], 'disposition': 'matched',
                'project_id': projects[0]['id'], 'reason': 'Fictional progress lifecycle check.'} for unit in units]), 'Controlled progress fixture'

        def analyze(self, goal, evidence, decisions):
            import time
            from app.contracts import Analysis
            time.sleep(2)
            return Analysis(findings=[], limitations=['Fictional progress lifecycle check, not model-quality verification.']), 'Controlled progress fixture'

    database = ROOT / 'artifacts' / ('browser-test-' + uuid4().hex + '.sqlite3')
    app = create_app(database, providers=ProgressProviders() if args.progress_fixture else OfflineProviders(), load_settings=False)
    print('Fictional browser tests only; models are disabled. Fresh isolated database: ' + str(database), flush=True)
    uvicorn.run(app, host='127.0.0.1', port=port, access_log=False, log_level='warning')


if __name__ == '__main__':
    main()
