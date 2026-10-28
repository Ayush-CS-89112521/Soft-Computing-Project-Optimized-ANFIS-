import csv
from collections import defaultdict

with open("cache_results_results.csv", "r") as f:
    rows = list(csv.DictReader(f))

workloads_to_print = [
    "Cyclic_Loop (Stress)",
    "cyclic",
    "Scan_Dominated (Sequential)",
    "scan",
    "phase_shift",
    "zipfian",
    "UMass_WebSearch1 (Search)",
    "CloudPhysics_w01 (FAST '15)"
]

policies = ["LFU", "StaticFuzzy", "FIFO", "2Q", "LRU", "ARC", "FastLutAnfis"]
capacities = ["32", "64", "128", "256", "512"]

for wl in workloads_to_print:
    print(f"\n==========================================================================================")
    print(f" WORKLOAD: {wl}")
    print(f"==========================================================================================")
    header = f"{'Capacity (C)':<14}" + "".join([f"{p:>12}" for p in policies])
    print(header)
    print("-" * len(header))
    
    # calculate average across seeds if synthetic
    data = defaultdict(list)
    for r in rows:
        if r["workload"] == wl:
            data[(r["capacity"], r["policy"])].append(float(r["hit_rate_pct"]))
            
    for cap in capacities:
        row_str = f"C = {cap:<8}"
        for p in policies:
            vals = data.get((cap, p), [])
            if vals:
                mean_val = sum(vals) / len(vals)
                row_str += f"{mean_val:>11.2f}%"
            else:
                row_str += f"{'N/A':>12}"
        print(row_str)
