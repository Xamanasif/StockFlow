"""Invoice-line validation. Cancellation rows stay visible; no invented inventory."""
import hashlib
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def code_hash():
    paths=sorted([*ROOT.glob('app/*.py'),*ROOT.glob('scripts/*.py'),*ROOT.glob('app/static/*')])
    return hashlib.sha256(''.join(str(p.relative_to(ROOT))+hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()).encode()).hexdigest()

COLUMNS = ['invoice', 'sku', 'date', 'quantity', 'unit_price']
ALIASES = {'Invoice': 'invoice', 'InvoiceNo': 'invoice', 'StockCode': 'sku',
           'InvoiceDate': 'date', 'Quantity': 'quantity', 'Price': 'unit_price',
           'UnitPrice': 'unit_price'}

def validate(frame):
    frame = frame.rename(columns=ALIASES).copy()
    missing = set(COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError('Missing columns: ' + ', '.join(sorted(missing)))
    # Drop unneeded customer information before storing canonical data.
    frame = frame[COLUMNS].copy()
    for name in ['invoice', 'sku']:
        if frame[name].isna().any():
            raise ValueError(f'{name} contains missing identifiers')
        frame[name] = frame[name].astype(str).str.strip()
        if frame[name].eq('').any():
            raise ValueError(f'{name} contains empty identifiers')
    frame['date'] = pd.to_datetime(frame['date'], errors='coerce')
    if frame['date'].isna().any():
        raise ValueError('Invalid transaction date')
    frame['date'] = frame['date'].dt.normalize()
    for name in ['quantity', 'unit_price']:
        frame[name] = pd.to_numeric(frame[name], errors='coerce')
        if (frame[name].isna() | ~frame[name].between(-1e9, 1e9)).any():
            raise ValueError(f'{name} must contain finite bounded numbers')
    if frame['quantity'].mod(1).ne(0).any():
        raise ValueError('Fractional quantities are unsupported in this prototype')
    if frame['unit_price'].lt(0).any():
        raise ValueError('Negative unit price requires manual review')
    frame['is_cancellation'] = frame['invoice'].str.upper().str.startswith('C')
    frame['is_adjustment'] = frame['quantity'].le(0) & ~frame['is_cancellation']
    frame['is_sale'] = (~frame['is_cancellation']) & frame['quantity'].gt(0) & frame['unit_price'].gt(0)
    audit = {'rows': len(frame), 'sale_rows': int(frame.is_sale.sum()),
             'cancellation_rows': int(frame.is_cancellation.sum()),
             'adjustment_rows': int(frame.is_adjustment.sum()),
             'zero_price_rows': int(frame.unit_price.eq(0).sum()),
             'possible_duplicate_rows': int(frame.duplicated(COLUMNS).sum()),
             'duplicate_policy': 'Flag only: identical invoice lines may be legitimate.'}
    return frame, audit

def load_dataset(path=None):
    path = Path(path or ROOT / 'data/demo_transactions.csv')
    meta_path = path.with_suffix('.meta.json')
    if not meta_path.exists():
        raise ValueError('Dataset provenance sidecar is required')
    metadata = json.loads(meta_path.read_text(encoding='utf-8'))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != metadata.get('sha256'):
        raise ValueError('Dataset checksum does not match provenance sidecar')
    frame, audit = validate(pd.read_csv(path))
    if not frame.is_sale.any():
        raise ValueError('No eligible positive-price sales')
    return frame, audit, metadata

