-- StockFlow: parameterized examples for the development-only analytics mart.
-- Bind :run_id and :sku using sqlite3.execute(sql, parameters), never interpolation.

-- 1. Reconcile loaded transaction and daily-positive-unit totals.
SELECT r.run_id,
       json_extract(r.accounting, '$.loaded_rows') AS expected_rows,
       (SELECT COUNT(*) FROM fact_transaction t WHERE t.run_id=r.run_id) AS actual_rows,
       json_extract(r.accounting, '$.positive_sale_units') AS expected_units,
       (SELECT SUM(d.recorded_units) FROM fact_daily_sales d WHERE d.run_id=r.run_id) AS daily_units
FROM mart_runs r WHERE r.run_id=:run_id;

-- 2. Explain exclusions without netting cancellations against observed sales.
SELECT sku, SUM(is_sale) AS sale_rows, SUM(is_cancellation) AS cancellation_rows,
       SUM(is_adjustment) AS adjustment_rows,
       SUM(CASE WHEN is_sale=1 THEN quantity ELSE 0 END) AS recorded_sale_units
FROM fact_transaction WHERE run_id=:run_id GROUP BY sku ORDER BY recorded_sale_units DESC;

-- 3. Calendar-complete preceding sales: current target never enters the lag.
SELECT sku,day,recorded_units,
       SUM(recorded_units) OVER(PARTITION BY run_id,sku ORDER BY day
           ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING) AS preceding_seven_day_units
FROM fact_daily_sales WHERE run_id=:run_id AND sku=:sku ORDER BY day;

-- 4. Development-only ABC ranking within selected products, not financial value.
SELECT sku, development_units, total_units, cumulative_units, abc_class
FROM v_development_abc WHERE run_id=:run_id ORDER BY development_units DESC,sku;

-- 5. Distinguish assumed zeros from actual observed sale-day evidence.
SELECT p.sku,p.first_sale,p.last_sale,p.calendar_days,p.assumed_zero_days,
       1.0*p.assumed_zero_days/p.calendar_days AS assumed_zero_fraction
FROM v_product_summary p WHERE run_id=:run_id ORDER BY assumed_zero_fraction DESC,p.sku;
