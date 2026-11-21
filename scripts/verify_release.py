"""One-command verification with actual outcomes and isolated-environment checks."""
import argparse
from datetime import datetime, timezone
from importlib.metadata import version, PackageNotFoundError
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

from app.data import ROOT, code_hash
from app.registry import sha


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--require-isolated',action='store_true')
    parser.add_argument('--browser',action='store_true')
    args=parser.parse_args()
    isolated=sys.prefix!=sys.base_prefix
    cfg=Path(sys.prefix)/'pyvenv.cfg'
    system_site=cfg.exists() and 'include-system-site-packages = true' in cfg.read_text().lower()
    if args.require_isolated and (not isolated or system_site):
        raise SystemExit('Create an isolated venv without system site packages; run its python -m scripts.verify_release --require-isolated --browser')
    directory=ROOT/'artifacts/releases'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    directory.mkdir(parents=True,exist_ok=False)
    source=code_hash()
    protected=[ROOT/'artifacts/real-final.json',ROOT/'artifacts/exploratory-robustness.json',*sorted((ROOT/'artifacts').glob('FINAL-*.json'))]
    before={str(p.relative_to(ROOT)):sha(p) for p in protected if p.exists()}
    env={**os.environ,'GROQ_API_KEY':''}
    env.pop('STOCKFLOW_CSV',None)
    commands=[('dependencies',[sys.executable,'-m','pip','check']),
              ('unit_api',[sys.executable,'-m','unittest','discover','-s','tests','-v']),
              ('lint',[sys.executable,'-m','ruff','check','app','scripts','tests','--select','F']),
              ('compile',[sys.executable,'-m','compileall','-q','app','scripts','tests'])]
    if args.browser:
        commands.append(('browser',[sys.executable,'-m','scripts.browser_test']))
    outcomes=[]
    for name,command in commands:
        start=time.monotonic()
        try:
            result=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=600)
            output=result.stdout+result.stderr
            code=result.returncode
        except subprocess.TimeoutExpired:
            output='Verification exceeded 600 seconds; no passing outcome asserted.'
            code=-1
        (directory/(name+'.txt')).write_text(output,encoding='utf-8')
        entry={'check':name,'command':command,'exit_code':code,'seconds':round(time.monotonic()-start,3)}
        if name=='unit_api':
            count=re.search(r'Ran (\d+) tests',output)
            entry['tests']=int(count[1]) if count else None
        outcomes.append(entry)
        print(json.dumps(entry),flush=True)
    after={str(p.relative_to(ROOT)):sha(p) for p in protected if p.exists()}
    packages={}
    for name in ['fastapi','pandas','numpy','scikit-learn','scipy','pydantic','playwright','ruff']:
        try:packages[name]=version(name)
        except PackageNotFoundError:packages[name]=None
    passed=all(o['exit_code']==0 for o in outcomes) and source==code_hash() and before==after
    report={'utc':datetime.now(timezone.utc).isoformat(),'status':'passed' if passed else 'failed',
            'command':'python -m scripts.verify_release '+' '.join(sys.argv[1:]),'python_executable':sys.executable,
            'python_version':platform.python_version(),'platform':platform.platform(),'isolated_environment':isolated,
            'system_site_packages_enabled':system_site,'browser_requested':args.browser,'package_versions':packages,
            'requirements_sha256':sha(ROOT/'requirements.lock'),'code_sha256':source,'source_unchanged':source==code_hash(),
            'protected_before':before,'protected_after':after,'checks':outcomes,
            'limits':'Local verification only; no cloud deployment, external users, live provider accuracy or business savings inferred.'}
    (directory/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'status':report['status'],'report':str(directory/'report.json')}))
    if not passed:
        raise SystemExit(1)


if __name__=='__main__':
    main()
