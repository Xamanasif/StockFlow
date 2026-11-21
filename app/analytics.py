"""Transactional SQL mart for recorded-sales evidence, separate from proposal storage."""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

import pandas as pd

from .data import validate, COLUMNS

SCHEMA = """
CREATE TABLE IF NOT EXISTS mart_runs (
 run_id TEXT PRIMARY KEY, dataset_sha256 TEXT NOT NULL, cutoff TEXT NOT NULL,
 created_utc TEXT NOT NULL, schema_version INTEGER NOT NULL, accounting TEXT NOT NULL,
 UNIQUE(dataset_sha256,cutoff)
);
CREATE TABLE IF NOT EXISTS dim_product (
 run_id TEXT NOT NULL REFERENCES mart_runs(run_id), sku TEXT NOT NULL,
 first_sale TEXT NOT NULL, last_sale TEXT NOT NULL,
 PRIMARY KEY(run_id,sku)
);
CREATE TABLE IF NOT EXISTS fact_transaction (
 run_id TEXT NOT NULL REFERENCES mart_runs(run_id), canonical_row INTEGER NOT NULL,
 invoice TEXT NOT NULL, sku TEXT NOT NULL, day TEXT NOT NULL,
 quantity INTEGER NOT NULL, unit_price_gbp REAL NOT NULL CHECK(unit_price_gbp>=0),
 is_sale INTEGER NOT NULL CHECK(is_sale IN (0,1)),
 is_cancellation INTEGER NOT NULL CHECK(is_cancellation IN (0,1)),
 is_adjustment INTEGER NOT NULL CHECK(is_adjustment IN (0,1)),
 PRIMARY KEY(run_id,canonical_row)
);
CREATE INDEX IF NOT EXISTS ix_transaction_product_date ON fact_transaction(run_id,sku,day);
CREATE TABLE IF NOT EXISTS fact_daily_sales (
 run_id TEXT NOT NULL, sku TEXT NOT NULL, day TEXT NOT NULL,
 recorded_units INTEGER NOT NULL CHECK(recorded_units>=0),
 observed_sale_value_gbp REAL NOT NULL CHECK(observed_sale_value_gbp>=0),
 assumed_zero INTEGER NOT NULL CHECK(assumed_zero IN (0,1)),
 PRIMARY KEY(run_id,sku,day),
 FOREIGN KEY(run_id,sku) REFERENCES dim_product(run_id,sku)
);
CREATE VIEW IF NOT EXISTS v_daily_evidence AS
 SELECT *, SUM(recorded_units) OVER (
 PARTITION BY run_id,sku ORDER BY day ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
 ) AS preceding_seven_day_units FROM fact_daily_sales;
CREATE VIEW IF NOT EXISTS v_product_summary AS
 SELECT p.run_id,p.sku,p.first_sale,p.last_sale,
 COUNT(*) AS calendar_days,SUM(d.recorded_units) AS recorded_units,
 SUM(d.assumed_zero) AS assumed_zero_days,
 SUM(d.observed_sale_value_gbp) AS approximate_observed_sale_value_gbp
 FROM dim_product p JOIN fact_daily_sales d ON p.run_id=d.run_id AND p.sku=d.sku
 GROUP BY p.run_id,p.sku;
CREATE VIEW IF NOT EXISTS v_development_abc AS
 WITH volumes AS (
 SELECT t.run_id,t.sku,SUM(t.quantity) AS development_units
 FROM fact_transaction t JOIN mart_runs r ON t.run_id=r.run_id
 WHERE t.is_sale=1 AND t.day<=date(json_extract(r.accounting,'$.selection_start'),'+59 days')
 GROUP BY t.run_id,t.sku
 ), ranked AS (
 SELECT *,SUM(development_units) OVER(PARTITION BY run_id) AS total_units,
 SUM(development_units) OVER(PARTITION BY run_id ORDER BY development_units DESC,sku
 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_units FROM volumes
 ) SELECT *,CASE WHEN total_units=0 THEN 'undefined'
 WHEN 1.0*(cumulative_units-development_units)/total_units<0.8 THEN 'A'
 WHEN 1.0*(cumulative_units-development_units)/total_units<0.95 THEN 'B' ELSE 'C' END AS abc_class
 FROM ranked;
"""


def build_mart(frame, metadata, path, cutoff=None):
    """Load one immutable source/cutoff exactly once; rollback fact writes on failure."""
    frame, _ = validate(frame[COLUMNS])
    cutoff = pd.Timestamp(cutoff) if cutoff is not None else frame.date.max()-pd.Timedelta(days=8)
    if cutoff > frame.date.max()-pd.Timedelta(days=8):
        raise ValueError('Analytics cutoff must exclude original final target window')
    limited = frame[frame.date <= cutoff].copy()
    if not limited.is_sale.any():
        raise ValueError('No sales before analytics cutoff')
    dataset_hash = metadata['sha256']
    cutoff_text = str(cutoff.date())
    run_id = hashlib.sha256((dataset_hash+':'+cutoff_text+':mart-v1').encode()).hexdigest()
    accounting = {'input_canonical_rows': len(frame), 'loaded_rows': len(limited),
                  'excluded_later_rows': len(frame)-len(limited),
                  'positive_sale_units': int(limited.loc[limited.is_sale, 'quantity'].sum()),
                  'selection_start': str(frame.date.min().date()),
                  'scope': 'selected canonical products, through development cutoff only',
                  'zero_fill': 'zero recorded sales assumed after first sale, not verified zero demand',
                  'value_units': 'approximate GBP observed sales value; not procurement cost/profit'}
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path, timeout=15)) as con:
        con.execute('PRAGMA foreign_keys=ON')
        con.executescript(SCHEMA)
        with con:
            con.execute('BEGIN IMMEDIATE')
            existing = con.execute('SELECT run_id FROM mart_runs WHERE dataset_sha256=? AND cutoff=?',
                                   (dataset_hash, cutoff_text)).fetchone()
            if existing:
                return {'run_id': existing[0], 'status': 'existing_immutable_version', 'accounting': accounting}
            con.execute('INSERT INTO mart_runs VALUES(?,?,?,?,?,?)',
                        (run_id, dataset_hash, cutoff_text, datetime.now(timezone.utc).isoformat(), 1, json.dumps(accounting)))
            con.executemany('INSERT INTO fact_transaction VALUES(?,?,?,?,?,?,?,?,?,?)',
                ((run_id, ordinal, str(row.invoice), str(row.sku), str(row.date.date()),
                  int(row.quantity), float(row.unit_price), int(row.is_sale), int(row.is_cancellation), int(row.is_adjustment))
                 for ordinal, row in enumerate(limited.itertuples(index=False))))
            con.execute('INSERT INTO dim_product SELECT run_id,sku,MIN(day),MAX(day) FROM fact_transaction WHERE run_id=? AND is_sale=1 GROUP BY run_id,sku', (run_id,))
            products = con.execute('SELECT sku,first_sale FROM dim_product WHERE run_id=?', (run_id,)).fetchall()
            for sku, first in products:
                con.executemany('INSERT INTO fact_daily_sales VALUES(?,?,?,0,0,1)',
                                ((run_id, sku, str(day.date())) for day in pd.date_range(first, cutoff)))
            con.execute('''WITH observed AS (
              SELECT sku,day,SUM(quantity) AS units,SUM(quantity*unit_price_gbp) AS value
              FROM fact_transaction WHERE run_id=? AND is_sale=1 GROUP BY sku,day
            ) UPDATE fact_daily_sales SET
              recorded_units=COALESCE((SELECT units FROM observed o WHERE o.sku=fact_daily_sales.sku AND o.day=fact_daily_sales.day),0),
              observed_sale_value_gbp=COALESCE((SELECT value FROM observed o WHERE o.sku=fact_daily_sales.sku AND o.day=fact_daily_sales.day),0),
              assumed_zero=CASE WHEN EXISTS(SELECT 1 FROM observed o WHERE o.sku=fact_daily_sales.sku AND o.day=fact_daily_sales.day) THEN 0 ELSE 1 END
              WHERE run_id=?''', (run_id, run_id))
            rows, units = con.execute('SELECT COUNT(*),COALESCE(SUM(CASE WHEN is_sale=1 THEN quantity ELSE 0 END),0) FROM fact_transaction WHERE run_id=?', (run_id,)).fetchone()
            daily_units = con.execute('SELECT COALESCE(SUM(recorded_units),0) FROM fact_daily_sales WHERE run_id=?', (run_id,)).fetchone()[0]
            if rows != len(limited) or units != accounting['positive_sale_units'] or daily_units != units:
                raise ValueError('SQL/Python reconciliation failure; transaction rolled back')
    return {'run_id': run_id, 'status': 'created', 'accounting': accounting}


def read_report(path, dataset_hash):
    """Parameterised, read-only reports; no user-supplied SQL or database path API."""
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError('Build analytics with python -m scripts.build_analytics')
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)) as con:
        con.row_factory = sqlite3.Row
        run = con.execute('SELECT * FROM mart_runs WHERE dataset_sha256=? ORDER BY cutoff DESC LIMIT 1', (dataset_hash,)).fetchone()
        if not run:
            raise LookupError('No analytics for active dataset; build this dataset first')
        products = [dict(r) for r in con.execute('SELECT p.*,a.development_units,a.abc_class FROM v_product_summary p LEFT JOIN v_development_abc a ON p.run_id=a.run_id AND p.sku=a.sku WHERE p.run_id=? ORDER BY p.recorded_units DESC,p.sku', (run['run_id'],))]
        totals = dict(con.execute('SELECT COUNT(*) AS transaction_rows,SUM(is_sale) AS sale_rows,SUM(is_cancellation) AS cancellation_rows,SUM(is_adjustment) AS adjustment_rows FROM fact_transaction WHERE run_id=?', (run['run_id'],)).fetchone())
        recent = [dict(r) for r in con.execute('SELECT * FROM v_daily_evidence WHERE run_id=? ORDER BY day DESC,sku LIMIT 35', (run['run_id'],))]
        return {'run_id': run['run_id'], 'dataset_sha256': dataset_hash, 'cutoff': run['cutoff'],
                'accounting': json.loads(run['accounting']), 'totals': totals, 'products': products, 'recent_daily': recent,
                'limitations': 'Development-only selected-product mart. Zero-fill assumed. ABC uses first-60-day units within the selected subset. Sale value is descriptive and approximate; it is not profit.'}
