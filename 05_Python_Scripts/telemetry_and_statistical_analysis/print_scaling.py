import csv
from collections import defaultdict

with open("cache_results_results.csv", "r") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

targets = [
    "CloudPhysics_w02 (FAST '15)",
    "UMass_Financial1 (OLTP)",
    "UMass_WebSearch1 (Search)",
    "SNIA_MSR_hm0 (Enterprise)"
]

policies = ["LFU", "StaticFuzzy", "FIFO", "2Q", "LRU", "ARC", "FastLutAnfis"]
capacities = ["32", "64", "128", "256", "512"]

for wl in targets:
    print(f"\n=======================================================")
    print(f" WORKLOAD: {wl}")
    print(f"=======================================================")
    header = f"{'Capacity (C)':<14}" + "".join([f"{p:>14}" for p in policies])
    print(header)
    print("-" * len(header))
    
    # map (cap, policy) -> hit_rate
    hit_map = {}
    for r in rows:
        if r["workload"] == wl:
            hit_map[(r["capacity"], r["policy"])] = float(r["hit_rate_pct"])
            
    for cap in capacities:
        row_str = f"C = {cap:<8}"
        for p in policies:
            hr = hit_map.get((cap, p), 0.0)
            row_str += f"{hr:>13.2f}%"
        print(row_str)
