"""Exploratory development extension; never calls original final evaluation."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import sys

import scipy
import sklearn

from app.data import ROOT, code_hash, load_dataset
from app.registry import sha
from app.research import METHODS, select_products
from app.simulation import Scenario, compare
from app.statistics import extended_folds, paired_block_comparison, summarize, summarize_policy_seeds


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=Path)
    parser.add_argument('--weeks', type=int, default=13)
    parser.add_argument('--output', type=Path, default=ROOT/'artifacts/exploratory-robustness.json')
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Choose a new output name; exploratory evidence is never overwritten')
    source_at_start = code_hash()
    frame, _, metadata = load_dataset(args.data)
    protected = [ROOT/'artifacts/real-final.json', *sorted((ROOT/'artifacts').glob('FINAL-*.json'))]
    before = {str(p.relative_to(ROOT)): sha(p) for p in protected if p.exists()}
    evaluation = extended_folds(frame, args.weeks)
    if evaluation['failures']:
        raise ValueError('Incomplete coverage: investigate failures before paired comparison: '+str(evaluation['failures']))
    comparisons = [paired_block_comparison(evaluation['rows'], method, block_weeks=length)
                   for method in METHODS if method != 'weekday_mean' for length in [1, 2, 3]]
    runs = []
    for seed in range(2026, 2031):
        runs.extend(compare(frame, select_products(frame), Scenario(seed=seed)))
    after = {str(p.relative_to(ROOT)): sha(p) for p in protected if p.exists()}
    if before != after:
        raise ValueError('Original final evidence changed during exploratory study')
    if source_at_start != code_hash():
        raise ValueError('Source changed during research; rerun to a new exploratory output after editing stops')
    result = {'utc': datetime.now(timezone.utc).isoformat(), 'command': 'python -m scripts.robustness '+' '.join(sys.argv[1:]),
              'scope': 'exploratory, specified after original final inspection; no new confirmatory holdout',
              'dataset_sha256': metadata['sha256'], 'code_sha256': source_at_start,
              'protocol_sha256': sha(ROOT/'docs/EXPLORATORY_PROTOCOL_V2.md'), 'seed': 20261121,
              'versions': {'python': platform.python_version(), 'scipy': scipy.__version__, 'scikit_learn': sklearn.__version__},
              'protected_final_before': before, 'protected_final_after': after,
              'evaluation': evaluation, 'forecast_summary': summarize(evaluation['rows']),
              'paired_resampling': comparisons, 'scenario_runs': runs, 'policy_summary': summarize_policy_seeds(runs)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False), encoding='utf-8')
    print(json.dumps({'output': str(args.output), 'forecast_summary': result['forecast_summary'], 'scenario_runs': len(runs), 'final_evidence_preserved': before == after}, indent=2))


if __name__ == '__main__':
    main()
