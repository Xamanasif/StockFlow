"""Sales baselines only. Zero-filled calendar dates are an explicit assumption."""
import numpy as np
import pandas as pd

def history(frame, sku, cutoff):
    cutoff = pd.Timestamp(cutoff).normalize()
    eligible = frame[(frame.date <= cutoff) & frame.is_sale]
    if eligible.empty:
        raise ValueError('No sales available at or before cutoff')
    observed = eligible[eligible.sku.eq(sku)].groupby('date').quantity.sum()
    if observed.empty:
        raise ValueError('Product has no observed sales before cutoff')
    calendar = pd.date_range(observed.index.min(), cutoff, freq='D')
    return observed.reindex(calendar, fill_value=0).astype(float)

def predict(frame, sku, cutoff, horizon=14, method='weekday_mean'):
    series = history(frame, sku, cutoff)
    if len(series) < 14:
        raise ValueError('At least 14 calendar days required')
    dates = pd.date_range(pd.Timestamp(cutoff) + pd.Timedelta(days=1), periods=horizon)
    if method == 'mean_28':
        values = [float(series.tail(28).mean())] * horizon
    elif method == 'weekday_mean':
        window = series.tail(56)
        values = [float(window[window.index.dayofweek == day.dayofweek].mean()) for day in dates]
    else:
        raise ValueError('Unknown baseline')
    return [{'date': d.date().isoformat(), 'units': round(max(0, v), 4)} for d, v in zip(dates, values)]

def backtest(frame, sku, origins=3, horizon=7):
    # SKU selection for the dashboard is not a research selection protocol.
    last = frame.date.max()
    folds = []
    for offset in range(origins, 0, -1):
        cutoff = last - pd.Timedelta(days=offset * horizon)
        actual_series = history(frame, sku, last)
        for method in ['mean_28', 'weekday_mean']:
            try:
                predictions = predict(frame, sku, cutoff, horizon, method)
            except ValueError:
                continue
            dates = pd.to_datetime([x['date'] for x in predictions])
            actual = actual_series.reindex(dates, fill_value=0).to_numpy()
            forecast = np.array([x['units'] for x in predictions])
            total = float(actual.sum())
            folds.append({'cutoff': cutoff.date().isoformat(), 'method': method,
                          'observations': horizon, 'actual_units': total,
                          'absolute_error': float(abs(actual - forecast).sum()),
                          'signed_error': float((forecast - actual).sum()),
                          'wape': None if total == 0 else float(abs(actual - forecast).sum() / total)})
    return folds

