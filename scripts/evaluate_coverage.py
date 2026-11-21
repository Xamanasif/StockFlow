"""Evaluate frozen methods on the pre-published expanded cohort; preserve old evidence."""
from datetime import datetime, timezone
import json
import platform

from app.coverage import coverage_study
from app.data import ROOT, code_hash, load_dataset
from app.registry import sha


def main():
    output=ROOT/'artifacts/coverage-study-v3a.json'
    if output.exists():
        raise SystemExit('Choose a new protocol/version; coverage evidence is immutable')
    source_hash=code_hash()
    selection=json.loads((ROOT/'artifacts/coverage-selection-v3a.json').read_text(encoding='utf-8'))
    protocol_hash=sha(ROOT/'docs/COVERAGE_PROTOCOL_V3A.md')
    if selection['protocol_sha256']!=protocol_hash:
        raise ValueError('Selection protocol changed after publication')
    protected=[ROOT/'artifacts/real-final.json',ROOT/'artifacts/exploratory-robustness.json',*sorted((ROOT/'artifacts').glob('FINAL-*.json'))]
    before={str(p.relative_to(ROOT)):sha(p) for p in protected}
    frame,_,metadata=load_dataset(selection['canonical'])
    study=coverage_study(frame,selection['selection'])
    after={str(p.relative_to(ROOT)):sha(p) for p in protected}
    if before!=after or source_hash!=code_hash():
        raise ValueError('Source or protected evidence changed during coverage evaluation')
    result={'utc':datetime.now(timezone.utc).isoformat(),'command':'python -m scripts.evaluate_coverage',
            'python':platform.python_version(),'dataset_sha256':metadata['sha256'],'code_sha256':source_hash,
            'protocol_sha256':protocol_hash,'selection_sha256':sha(ROOT/'artifacts/coverage-selection-v3a.json'),
            'protected_before':before,'protected_after':after,'study':study}
    output.write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({'products':study['product_count'],'summary':study['summary'],'failures':len(study['failures']),
                      'complete_paired_coverage':study['complete_paired_coverage']},indent=2))


if __name__=='__main__':
    main()
