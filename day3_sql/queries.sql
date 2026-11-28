-- Q1: Top 5 vendors by total paid spend
SELECT
    vendor_name,
    COUNT(*) AS payment_count,
    SUM(amount) AS total_spend
FROM vendor_payments
WHERE status = 'paid'
GROUP BY vendor_name
ORDER BY total_spend DESC
LIMIT 5;

-- Q2: Duplicate invoice payments detected via ROW_NUMBER() window function
WITH ranked_invoices AS (
    SELECT
        payment_id,
        invoice_no,
        vendor_name,
        amount,
        payment_date,
        ROW_NUMBER() OVER (
            PARTITION BY invoice_no
            ORDER BY payment_date, payment_id
        ) AS rn
    FROM vendor_payments
    WHERE status = 'paid'
)
SELECT payment_id, invoice_no, vendor_name, amount, payment_date, rn
FROM ranked_invoices
WHERE rn > 1
ORDER BY invoice_no;

-- Q3: Monthly payment totals (paid invoices)
SELECT
    DATE_TRUNC('month', payment_date)::DATE AS payment_month,
    COUNT(*) AS payments,
    SUM(amount) AS monthly_total
FROM vendor_payments
WHERE status = 'paid'
GROUP BY payment_month
ORDER BY payment_month;

-- Q4: Late payments where payment_date is after due_date
SELECT
    payment_id,
    invoice_no,
    vendor_name,
    due_date,
    payment_date,
    (payment_date - due_date) AS days_late,
    amount
FROM vendor_payments
WHERE status = 'paid' AND payment_date > due_date
ORDER BY days_late DESC, amount DESC
LIMIT 15;

-- Q5: Total spend and average invoice size by expense category
SELECT
    category,
    COUNT(*) AS invoices,
    SUM(amount) AS total_spend,
    ROUND(AVG(amount), 2) AS avg_amount
FROM vendor_payments
WHERE status = 'paid'
GROUP BY category
ORDER BY total_spend DESC;

-- Q6: High-volume vendors with more than 350 paid invoices (WHERE vs HAVING demo)
SELECT
    vendor_name,
    COUNT(*) AS paid_invoices,
    SUM(amount) AS total_spend
FROM vendor_payments
WHERE status = 'paid'
GROUP BY vendor_name
HAVING COUNT(*) > 350
ORDER BY paid_invoices DESC;

-- Q7: Breakdown of payments by status (paid, pending, disputed)
SELECT
    status,
    COUNT(*) AS row_count,
    SUM(amount) AS total_value
FROM vendor_payments
GROUP BY status
ORDER BY total_value DESC;

-- Q8: Vendors ranked by average days late on overdue invoices
SELECT
    vendor_name,
    COUNT(*) AS late_count,
    ROUND(AVG(payment_date - due_date), 1) AS avg_days_late,
    SUM(amount) AS late_spend
FROM vendor_payments
WHERE status = 'paid' AND payment_date > due_date
GROUP BY vendor_name
ORDER BY avg_days_late DESC;

-- Q9: High-value outlier payments exceeding 1.8x the overall average amount
SELECT
    payment_id,
    invoice_no,
    vendor_name,
    category,
    amount
FROM vendor_payments
WHERE amount > 1.8 * (SELECT AVG(amount) FROM vendor_payments)
ORDER BY amount DESC
LIMIT 15;

-- Q10: Running cumulative monthly spend across the year (window SUM)
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', payment_date)::DATE AS payment_month,
        SUM(amount) AS monthly_total
    FROM vendor_payments
    WHERE status = 'paid'
    GROUP BY payment_month
)
SELECT
    payment_month,
    monthly_total,
    SUM(monthly_total) OVER (ORDER BY payment_month) AS cumulative_spend
FROM monthly
ORDER BY payment_month;

-- STEP 4A: Query plan BEFORE adding an index
DROP INDEX IF EXISTS idx_vendor_payments_vendor_date;
EXPLAIN ANALYZE
SELECT payment_id, invoice_no, amount, payment_date
FROM vendor_payments
WHERE vendor_name = 'Apex Electricals'
  AND payment_date >= '2026-09-01';

-- STEP 4B: Create composite index on (vendor_name, payment_date) and update planner stats
CREATE INDEX idx_vendor_payments_vendor_date
    ON vendor_payments (vendor_name, payment_date);
ANALYZE vendor_payments;

-- STEP 4C: Query plan AFTER adding the index
EXPLAIN ANALYZE
SELECT payment_id, invoice_no, amount, payment_date
FROM vendor_payments
WHERE vendor_name = 'Apex Electricals'
  AND payment_date >= '2026-09-01';