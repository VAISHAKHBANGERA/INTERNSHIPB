import csv
import json
import time
from pathlib import Path

# Change: from triager import triage_complaint
from day5_triager.triager import triage_complaint

BASE_DIR = Path(__file__).parent
SAMPLES_PATH = BASE_DIR / "samples.json"
OUTPUT_CSV = BASE_DIR / "accuracy.csv"


def hospital_matches(predicted: str | None, expected: str | None) -> bool:
    if expected is None:
        return predicted is None
    if predicted is None:
        return False
    p, e = predicted.lower().strip(), expected.lower().strip()
    return e in p or p in e


def equipment_matches(predicted: str, keyword: str) -> bool:
    return keyword.lower() in predicted.lower()


def run_eval() -> None:
    samples = json.loads(SAMPLES_PATH.read_text(encoding="utf-8"))
    rows: list[dict[str, object]] = []
    v1_correct = 0
    v2_correct = 0

    for sample in samples:
        sid = sample["id"]
        complaint = sample["complaint"]
        exp_eq = sample["expected_equipment_keyword"]
        exp_urg = sample["expected_urgency"]
        exp_hosp = sample["expected_hospital"]

        res_v1, att_v1 = triage_complaint(complaint, version="v1")
        time.sleep(1.0)  # Gentle pacing for Groq free-tier rate limits
        res_v2, att_v2 = triage_complaint(complaint, version="v2")
        time.sleep(1.0)

        v1_pass = (
            equipment_matches(res_v1.equipment, exp_eq)
            and res_v1.urgency.value == exp_urg
            and hospital_matches(res_v1.hospital, exp_hosp)
        )
        v2_pass = (
            equipment_matches(res_v2.equipment, exp_eq)
            and res_v2.urgency.value == exp_urg
            and hospital_matches(res_v2.hospital, exp_hosp)
        )

        v1_correct += int(v1_pass)
        v2_correct += int(v2_pass)

        print(
            f"Sample {sid:02d} | exp=({exp_urg}, {exp_hosp}) | "
            f"v1=({res_v1.urgency.value}, {res_v1.hospital}) {'PASS' if v1_pass else 'FAIL'} | "
            f"v2=({res_v2.urgency.value}, {res_v2.hospital}) {'PASS' if v2_pass else 'FAIL'}"
        )

        rows.append({
            "id": sid,
            "complaint": complaint,
            "expected_equipment": exp_eq,
            "expected_urgency": exp_urg,
            "expected_hospital": exp_hosp if exp_hosp is not None else "null",
            "v1_equipment": res_v1.equipment,
            "v1_urgency": res_v1.urgency.value,
            "v1_hospital": res_v1.hospital if res_v1.hospital is not None else "null",
            "v1_attempts": att_v1,
            "v1_pass": v1_pass,
            "v2_equipment": res_v2.equipment,
            "v2_urgency": res_v2.urgency.value,
            "v2_hospital": res_v2.hospital if res_v2.hospital is not None else "null",
            "v2_attempts": att_v2,
            "v2_pass": v2_pass,
        })

    total = len(samples)
    v1_pct = round((v1_correct / total) * 100, 1)
    v2_pct = round((v2_correct / total) * 100, 1)

    fieldnames = list(rows[0].keys())
    with OUTPUT_CSV.open(mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        writer.writerow({
            "id": "OVERALL",
            "complaint": f"Scored {total} samples",
            "v1_pass": f"{v1_correct}/{total} ({v1_pct}%)",
            "v2_pass": f"{v2_correct}/{total} ({v2_pct}%)",
        })

    print("\n=== EVALUATION SUMMARY ===")
    print(f"Prompt v1: {v1_correct}/{total} ({v1_pct}%)")
    print(f"Prompt v2: {v2_correct}/{total} ({v2_pct}%)")
    print(f"Saved results to {OUTPUT_CSV}")


if __name__ == "__main__":
    run_eval()