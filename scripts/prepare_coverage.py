"""Publish broader development-selected cohort before evaluating its outcomes."""
from datetime import datetime, timezone
import argparse
import json

from app.coverage import select_cohort
from app.data import ROOT, COLUMNS
from app.registry import read_raw, preview, publish, sha


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--version',choices=['v3','v3a'],default='v3a')
    args=parser.parse_args()
    protocol=ROOT/f'docs/COVERAGE_PROTOCOL_{args.version.upper()}.md'
    output=ROOT/f'artifacts/coverage-selection-{args.version}.json'
    if output.exists():
        raise SystemExit('Coverage selection already published; preserve it and use a new protocol/version')
    previous=json.loads((ROOT/'artifacts/real-import.json').read_text(encoding='utf-8'))
    excluded=previous['metadata']['products']
    source=ROOT/'data/raw/online_retail_II.xlsx'
    clean,rejected,audit=preview(read_raw(source))
    selection=select_cohort(clean,excluded=excluded,physical_codes_only=args.version=='v3a')
    snapshot=ROOT/f'data/raw/coverage-cohort-{args.version}.csv'
    quarantine=ROOT/f'data/raw/coverage-quarantine-{args.version}.csv'
    if snapshot.exists() or quarantine.exists():
        raise SystemExit('Staged v3 source exists; inspect before retrying rather than overwriting')
    clean.loc[clean.sku.isin([r['sku'] for r in selection['products']]),COLUMNS].to_csv(snapshot,index=False)
    # Explicit v3 protocol retains rejected source rows with reasons; no customer fields.
    rejected.to_csv(quarantine,index=False)
    canonical=publish(snapshot,source_url='https://archive.ics.uci.edu/dataset/502/online+retail+ii',license_name='CC BY 4.0',
                      extra_metadata={'coverage_protocol_sha256':sha(protocol),
                                      'original_workbook_sha256':sha(source),'original_row_accounting':audit,
                                      'original_quarantine_sha256':sha(quarantine),'coverage_selection':selection})
    result={'utc':datetime.now(timezone.utc).isoformat(),'command':f'python -m scripts.prepare_coverage --version {args.version}',
            'canonical':str(canonical),'dataset_sha256':sha(canonical),'protocol_sha256':sha(protocol),
            'original_workbook_sha256':sha(source),'source_row_accounting':{k:v for k,v in audit.items() if k!='product_entry_exit'},
            'selection':selection}
    output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'canonical':str(canonical),'selected_products':len(selection['products']),'strata':selection['strata']},indent=2))


if __name__=='__main__':
    main()
