import random
from datetime import date, timedelta
from pathlib import Path
import pandas as pd

random.seed(42)

VENDORS = [
    "Apex Electricals", "BlueLine HVAC", "CoreTech Solutions",
    "Delta Facilities", "Evergreen Supplies", "FastTrack Logistics",
    "GridPower Services", "Horizon Security", "Indus Plumbing", "JetClean Corp",
]
CATEGORIES = ["Maintenance", "IT", "Utilities", "Security", "Logistics"]
STATUSES = ["paid", "paid", "paid", "paid", "pending", "disputed"]

rows = []
start = date(2026, 1, 1)

for i in range(1, 4951):
    vendor = random.choice(VENDORS)
    invoice_date = start + timedelta(days=random.randint(0, 300))
    due_date = invoice_date + timedelta(days=30)
    delay = random.choices([-5, 0, 5, 15, 35], weights=[30, 35, 15, 12, 8])[0]
    payment_date = due_date + timedelta(days=delay)
    status = random.choice(STATUSES)

    rows.append({
        "payment_id": i,
        "invoice_no": f"INV-{10000 + i}",
        "vendor_name": vendor,
        "category": random.choice(CATEGORIES),
        "amount": round(random.uniform(500, 25000), 2),
        "invoice_date": invoice_date.isoformat(),
        "due_date": due_date.isoformat(),
        "payment_date": payment_date.isoformat() if status == "paid" else None,
        "status": status,
        "notes": None if random.random() < 0.25 else "Standard AMC settlement",
    })

# Inject 50 intentional duplicate invoice payouts for audit testing
for idx in range(50):
    dup = rows[idx * 20].copy()
    dup["payment_id"] = 4951 + idx
    dup["status"] = "paid"
    dup["payment_date"] = dup["due_date"]
    dup["notes"] = "Duplicate payout"
    rows.append(dup)

out_path = Path("day3_sql/data/vendor_payments.csv")
pd.DataFrame(rows).to_csv(out_path, index=False)
print(f"Generated {len(rows)} synthetic rows at {out_path}")