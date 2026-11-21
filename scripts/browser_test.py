"""Full browser workflow; starts and terminates its own isolated local server."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from playwright.sync_api import sync_playwright
from app.data import ROOT
from app.data import load_dataset, code_hash
from app.analytics import build_mart
from datetime import datetime, timezone

def main():
    with tempfile.TemporaryDirectory() as d:
        with socket.socket() as s: s.bind(('127.0.0.1',0)); port=s.getsockname()[1]
        frame,_,metadata=load_dataset()
        mart=Path(d)/'analytics.db'
        build_mart(frame,metadata,mart)
        env={**os.environ,'STOCKFLOW_DB':str(Path(d)/'browser.db'),'STOCKFLOW_CSV':str(ROOT/'data/demo_transactions.csv'),'GROQ_API_KEY':'','STOCKFLOW_ANALYTICS':str(mart)}
        process=subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',str(port)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        base=f'http://127.0.0.1:{port}'; checks=[]
        try:
            for _ in range(100):
                try:
                    urllib.request.urlopen(base+'/api/ready',timeout=1); break
                except OSError: time.sleep(.1)
            with sync_playwright() as p:
                browser=p.chromium.launch(headless=True,channel=os.environ.get("STOCKFLOW_BROWSER", "msedge"))
                page=browser.new_page(); errors=[]; page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(base); page.get_by_text('Ready. All inventory',exact=False).wait_for()
                with page.expect_response('**/api/datasets') as registry_response:
                    page.get_by_role('button',name='Refresh registry').click()
                assert registry_response.value.status==200
                page.locator('#datasetChoice option').first.wait_for(state='attached')
                page.get_by_role('button',name='Use selected dataset').click(); page.get_by_text('Ready. All inventory',exact=False).wait_for(); checks.append('registered dataset selection')
                page.get_by_text('Data quality and assumptions',exact=True).click(); assert 'synthetic_demo' in page.locator('#quality').inner_text(); checks.append('quality and provenance')
                page.get_by_role('button',name='Refresh history').click(); page.get_by_text('No saved proposals.',exact=True).wait_for(); checks.append('empty history state')
                page.get_by_role('button',name='Load SQL analytics').click()
                page.get_by_text('Mart evidence ID:',exact=False).wait_for(); checks.append('reconciled SQL analytics')
                if (ROOT/'artifacts/exploratory-robustness.json').exists():
                    page.get_by_role('button',name='Load robustness study').click()
                    page.get_by_role('columnheader',name='WAPE difference (pp)',exact=True).wait_for()
                    page.get_by_text('DIFFERENT DATASET:',exact=False).wait_for()
                    checks.append('exploratory study and mismatched-source warning')
                if (ROOT/'artifacts/coverage-study-v3a.json').exists():
                    page.get_by_role('button',name='Load broader coverage study').click()
                    page.get_by_role('columnheader',name='Mean MASE / defined folds',exact=True).wait_for()
                    checks.append('broader cohort coverage and scaled-error evidence')
                page.get_by_role('button',name='Inspect baseline forecasts').click(); page.locator('svg').wait_for(); checks.append('product evidence chart')
                page.locator('#budget').fill('100'); page.get_by_role('button',name='Build proposal').click()
                page.get_by_role('link',name='Open saved calculation snapshot').wait_for(); checks.append('assumptions and proposal')
                page.get_by_role('button',name='Compare policies',exact=True).click(); page.locator('#status').get_by_text('Ready.',exact=True).wait_for(timeout=120000); assert 'croston_sba' in page.locator('main').inner_text(); checks.append('policy cross comparison')
                page.get_by_role('button',name='Refresh history').click(); page.get_by_role('button',name='Pending',exact=False).first.click()
                run=page.locator('#planId').input_value()
                assert run
                page.get_by_role('button',name='Preview exact proposal').click(); page.get_by_text('Local unauthenticated human review',exact=False).wait_for()
                page.get_by_role('button',name='Confirm inspected version locally').click(); page.get_by_text('locally_confirmed_no_external_order',exact=False).wait_for(); checks.append('version-bound local confirmation')
                page.get_by_role('button',name='Explain selected proposal').click(); page.get_by_text('No GROQ_API_KEY;',exact=False).wait_for(); checks.append('offline cited assistant')
                page.get_by_role('button',name='Refresh history').click(); page.get_by_role('button',name='local unauthenticated confirmation',exact=False).wait_for(); checks.append('revisited reviewed history')
                page.locator('#budget').fill('-1'); page.get_by_role('button',name='Build proposal').click(); page.get_by_text('Enter a valid nonnegative budget.',exact=False).wait_for(); checks.append('validation error')
                page.evaluate('window.scrollTo(0,0)'); page.set_viewport_size({'width':390,'height':844}); page.screenshot(path=str(ROOT/'artifacts/mobile.png'),full_page=True); page.screenshot(path=str(ROOT/'artifacts/mobile-viewport.png')); assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'); checks.append('mobile rendering')
                page.set_viewport_size({'width':1440,'height':1000}); page.screenshot(path=str(ROOT/'artifacts/desktop.png'),full_page=True)
                assert not errors, errors
                browser.close()
            result={'status':'passed','checks':checks,'javascript_errors':errors,'command':'python -m scripts.browser_test',
                    'utc':datetime.now(timezone.utc).isoformat(),'code_sha256':code_hash(),'dataset_sha256':metadata['sha256'],
                    'scope':'headless '+os.environ.get('STOCKFLOW_BROWSER','msedge')+' on Windows; synthetic data; no live Groq'}
            (ROOT/'artifacts/browser.json').write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps(result,indent=2))
        finally:
            process.terminate(); process.wait(timeout=15)

if __name__=='__main__': main()
