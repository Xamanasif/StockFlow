# Actual saved worked example

Synthetic demo, assumed GBP procurement/stock. Run `43a5fa37-bff8-4bc8-9d83-bf546f8746f6`; snapshot `394fed457674558076150f4e5436c50b971e663adee06997eec17a9d727f5d47`.

For SKU-001, last seven calendar units are [11.0, 4.0, 10.0, 4.0, 8.0, 11.0, 4.0]. Lead+review=21 days, expected units=145.8750; stock=12, on-order=0, pack=6, MOQ=12. Rounded requested units=138; allocated=66; uncovered rounded target=72. Row cash=66 × 150 = 9900 pence.

Plan total spends 9900 of 10000 pence and reserves 126 units. Sum row spends and compare to this total. Full source rows, dates, forecast and inputs are in worked-trace.json; exact persisted response is worked-proposal.json. This is a constructed scenario, not a historical order.
