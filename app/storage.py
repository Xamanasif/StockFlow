"""Local review receipts with transactionally consumed version-bound challenges."""
from contextlib import contextmanager
import hashlib
import json
import os
import sqlite3
import time
import uuid
from pathlib import Path
from .data import ROOT

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,allow_nan=False).encode()).hexdigest()

@contextmanager
def db():
    path=Path(os.environ.get('STOCKFLOW_DB',ROOT/'data/stockflow.db')); path.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(path,timeout=10)
    try:
        con.executescript('''CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,created TEXT,hash TEXT,payload TEXT);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);
        CREATE TABLE IF NOT EXISTS assumptions(hash TEXT PRIMARY KEY,payload TEXT,created REAL);
        CREATE TABLE IF NOT EXISTS challenges(token TEXT PRIMARY KEY,run_id TEXT,hash TEXT,data_hash TEXT,assumptions_hash TEXT,expires REAL,used INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS reviews(run_id TEXT PRIMARY KEY,hash TEXT,created REAL,label TEXT);
        CREATE TABLE IF NOT EXISTS idempotency(key TEXT PRIMARY KEY,fingerprint TEXT,run_id TEXT);
        PRAGMA user_version=1;''')
        yield con
        con.commit()
    except BaseException:
        con.rollback(); raise
    finally: con.close()

def save_assumptions(con,assumptions):
    h=digest(assumptions)
    con.execute('INSERT OR IGNORE INTO assumptions VALUES(?,?,?)',(h,json.dumps(assumptions,sort_keys=True),time.time()))
    con.execute("INSERT OR REPLACE INTO settings VALUES('assumptions',?)",(h,))
    return h

def challenge(run_id,hash_value,data_hash,assumptions_hash):
    token=str(uuid.uuid4()); expires=time.time()+300
    with db() as con:
        con.execute('INSERT INTO challenges VALUES(?,?,?,?,?,?,0)',(token,run_id,hash_value,data_hash,assumptions_hash,expires))
    return {'token':token,'expires_epoch':expires,'run_id':run_id,'sha256':hash_value,'label':'Local unauthenticated human review; no identity assurance or external order'}

def confirm(token,expected_hash,current_data_hash):
    with db() as con:
        con.execute('BEGIN IMMEDIATE')
        row=con.execute('SELECT run_id,hash,data_hash,assumptions_hash,expires,used FROM challenges WHERE token=?',(token,)).fetchone()
        if not row: raise ValueError('Unknown review request')
        run_id,h,data_h,assumptions_h,expires,used=row
        active=con.execute("SELECT value FROM settings WHERE key='assumptions'").fetchone()
        saved=con.execute('SELECT hash,payload FROM runs WHERE id=?',(run_id,)).fetchone()
        if used or expires<time.time(): raise ValueError('Expired or reused review request')
        if h!=expected_hash or data_h!=current_data_hash or not active or active[0]!=assumptions_h:
            raise ValueError('Stale proposal: data, assumptions or version changed')
        if not saved or digest(json.loads(saved[1]))!=h or saved[0]!=h: raise ValueError('Snapshot integrity failure')
        if con.execute('SELECT 1 FROM reviews WHERE run_id=?',(run_id,)).fetchone(): raise ValueError('Already reviewed')
        con.execute('INSERT INTO reviews VALUES(?,?,?,?)',(run_id,h,time.time(),'local unauthenticated confirmation'))
        con.execute('UPDATE challenges SET used=1 WHERE token=?',(token,))
    return {'run_id':run_id,'sha256':h,'status':'locally_confirmed_no_external_order'}
