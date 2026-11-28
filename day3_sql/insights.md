# Day 3 — Vendor Payments Insights

1. **Top spend concentration:** `BlueLine HVAC` leads paid spend at **$4,320,185.25** across 344 invoices, followed closely by `Apex Electricals` ($4,318,474.90) and `Horizon Security` ($4,282,029.31), while `Security` ($8.64M) and `IT` ($8.63M) are the highest-spend categories (Q1 & Q5).

2. **Duplicate payout leakage:** Window-function auditing (`ROW_NUMBER() OVER (PARTITION BY invoice_no ...)`) flagged **28 duplicate paid invoices** across vendors such as `BlueLine HVAC` and `JetClean Corp` (Q2), highlighting the need for a unique constraint or pre-payment check on `invoice_no`.

3. **Late payment exposure:** Across all 10 vendors, **1,153 paid invoices** totaling **$14,393,601.57** were settled past their due date, with delays reaching **35 days** and `BlueLine HVAC` averaging the longest delay at **16.9 days** (Q4 & Q8).

4. **Unresolved payment backlog:** **1,672 non-paid records**—830 `disputed` ($10,718,797.45) and 842 `pending` ($10,186,755.85)—account for **$20,905,553.30** in unsettled obligations that require clearance before month-end close (Q7).

5. **Index & `EXPLAIN ANALYZE` impact:** Adding a composite index on `(vendor_name, payment_date)` replaced the full `Seq Scan` (cost `150.00`, scanning all 5,000 rows and discarding 4,902) with a `Bitmap Index Scan` (cost `85.74`, locating the exact 98 matching rows directly and reducing heap buffer hits from 75 to 55). First-run wall time (`2.024 ms` vs `0.746 ms`) was slightly higher only because the new index pages were read cold from disk (`shared read=3`) on a small 5,000-row table.