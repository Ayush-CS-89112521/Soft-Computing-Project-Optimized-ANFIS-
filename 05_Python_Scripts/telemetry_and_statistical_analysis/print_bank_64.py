import csv
from collections import defaultdict

def get_bank_summary(csv_file):
    with open(csv_file, "r") as f:
        rows = [r for r in csv.DictReader(f) if r["capacity"] == "64"]
    data = defaultdict(list)
    for r in rows:
        data[r["policy"]].append(float(r["hit_rate_pct"]))
    res = {}
    for p, vals in data.items():
        res[p] = sum(vals) / len(vals)
    return res, len(rows) // len(data) if data else 0

banks = {
    "Cyclic Loop Bank": "cyclic_mass_results.csv",
    "Zipfian Locality Bank": "zipfian_mass_results.csv",
    "Dynamic Phase-Shift Bank": "phase_shift_mass_results.csv",
    "Scan-Dominated Bank": "scan_mass_results.csv"
}

print("=== MASS BANK RESULTS AT C = 64 (500,000 requests per bank) ===")
for bname, bfile in banks.items():
    stats, num_traces = get_bank_summary(bfile)
    print(f"\n{bname} (Traces: {num_traces}, Total Requests: {num_traces * 25000:,}):")
    for p in ["Fast-LUT-ANFIS", "IBM-ARC", "LRU", "FIFO", "LFU"]:
        hr = stats.get(p, 0.0)
        print(f"  {p:<18}: {hr:6.2f}%")
