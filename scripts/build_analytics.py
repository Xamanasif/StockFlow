"""Build and reconcile development-only SQL analytics for a verified dataset."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from app.analytics import build_mart, read_report
from app.data import ROOT, code_hash, load_dataset


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=Path)
    parser.add_argument('--database', type=Path, default=ROOT/'data/analytics.db')
    parser.add_argument('--output', type=Path, default=ROOT/'artifacts/analytics.json')
    args = parser.parse_args()
    frame, _, metadata = load_dataset(args.data)
    loaded = build_mart(frame, metadata, args.database)
    result = {'utc': datetime.now(timezone.utc).isoformat(), 'code_sha256': code_hash(),
              'command': 'python -m scripts.build_analytics '+' '.join(__import__('sys').argv[1:]),
              'load': loaded, 'report': read_report(args.database, metadata['sha256'])}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise SystemExit('Choose a new output name; analytics evidence is never silently overwritten')
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False), encoding='utf-8')
    print(json.dumps({'output': str(args.output), 'run_id': loaded['run_id'], 'status': loaded['status'], 'accounting': loaded['accounting']}, indent=2))


if __name__ == '__main__':
    main()
