"""Download is separate; retain official workbook and derive development-selected subset."""
import argparse
import json
import zipfile
from app.registry import read_raw, preview, publish, sha
from app.research import select_products
from app.data import ROOT, COLUMNS

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--quarantine',action='store_true'); args=parser.parse_args()
    raw=ROOT/'data/raw'; archive=raw/'online-retail-ii.zip'
    with zipfile.ZipFile(archive) as z:
        name=next(n for n in z.namelist() if n.endswith('.xlsx'))
        target=raw/'online_retail_II.xlsx'
        if not target.exists():
            with target.open('xb') as out: out.write(z.read(name))
    frame=read_raw(target); clean,rejected,audit=preview(frame)
    if len(rejected) and not args.quarantine: raise SystemExit('Explicit --quarantine required; invalid source rows found')
    quarantine_path=raw/'uci-quarantine.csv'
    rejected.to_csv(quarantine_path,index=False)
    skus=select_products(clean); subset=raw/'uci-development-selected.csv'
    if not subset.exists(): clean.loc[clean.sku.isin(skus),COLUMNS].to_csv(subset,index=False)
    extra={'derivation':'Five SKUs selected on first 60 days, first sale by day 14; full original historical dates retained',
           'original_workbook_sha256':sha(target),'official_archive_sha256':sha(archive),'original_row_accounting':audit,
           'original_quarantine_rows':len(rejected),'original_quarantine_sha256':sha(quarantine_path),'products':skus}
    output=publish(subset,source_url='https://archive.ics.uci.edu/dataset/502/online+retail+ii',license_name='CC BY 4.0',extra_metadata=extra)
    meta_path=output.with_suffix('.meta.json'); meta=json.loads(meta_path.read_text(encoding='utf-8'))
    (ROOT/'artifacts/real-import.json').write_text(json.dumps({'canonical':str(output),'metadata':meta,'command':'python -m scripts.prepare_real --quarantine'},indent=2),encoding='utf-8')
    print(json.dumps({'canonical':str(output),'original_rows':len(frame),'selected_skus':skus,'quarantined':len(rejected)}))

if __name__=='__main__': main()
