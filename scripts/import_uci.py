"""Preview first; immutable publication with explicit quarantine."""
import argparse
import json
from pathlib import Path
from app.registry import preview, read_raw, publish

def main():
    p=argparse.ArgumentParser(); p.add_argument('source',type=Path)
    p.add_argument('--preview',action='store_true'); p.add_argument('--quarantine',action='store_true')
    p.add_argument('--registry',type=Path,default=Path('data/registry'))
    p.add_argument('--source-url',default='user supplied; unverified origin'); p.add_argument('--license',default='unverified')
    a=p.parse_args(); _,_,audit=preview(read_raw(a.source)); print(json.dumps(audit,indent=2))
    if not a.preview: print(publish(a.source,a.registry,a.quarantine,a.source_url,a.license))

if __name__=='__main__': main()
