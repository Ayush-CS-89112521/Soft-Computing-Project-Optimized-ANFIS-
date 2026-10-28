import csv
from collections import defaultdict

# 1. From fine_capacity_*.csv (Capacities 2 to 64)
suites = {
    "Scan": "fine_capacity_scandominated.csv",
    "Zipfian": "fine_capacity_zipfian.csv",
    "PhaseShift": "fine_capacity_phaseshift.csv"
}

fine_data = defaultdict(lambda: defaultdict(dict))
capacities_fine = [2, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64]
policies = ["LFU", "FIFO", "LRU", "ARC", "FastLUT_ANFIS"]

for sname, sfile in suites.items():
    with open(sfile, "r") as f:
        for r in csv.DictReader(f):
            c = int(r["capacity"])
            for p in policies:
                fine_data[sname][c][p] = float(r[p])

print("=" * 115)
print(" 3-WAY AVERAGE: SCAN-DOMINATED + ZIPFIAN + PHASE-SHIFTING (Fine-Grained C = 2 to 64)")
print("=" * 115)
print(f"{'Capacity (C)':<14} {'LFU':<10} {'FIFO':<10} {'LRU':<10} {'ARC':<10} {'Fast-LUT ANFIS':<16} {'vs LRU':<12} {'vs ARC':<12} {'Rank / Status'}")
print("-" * 115)

for c in capacities_fine:
    means = {}
    for p in policies:
        means[p] = (fine_data["Scan"][c][p] + fine_data["Zipfian"][c][p] + fine_data["PhaseShift"][c][p]) / 3.0
        
    anf = means["FastLUT_ANFIS"]
    lru = means["LRU"]
    arc = means["ARC"]
    fifo = means["FIFO"]
    lfu = means["LFU"]
    
    diff_lru = anf - lru
    diff_arc = anf - arc
    
    # rank among 5
    all_scores = [("ANFIS", anf), ("LRU", lru), ("ARC", arc), ("FIFO", fifo), ("LFU", lfu)]
    all_scores.sort(key=lambda x: x[1], reverse=True)
    rank = [x[0] for x in all_scores].index("ANFIS") + 1
    
    status = f"Rank #{rank}"
    if rank == 1:
        status += " (BETTER THAN ALL!)"
    elif diff_lru > 0 and abs(diff_arc) < 2.0:
        status += " (Beats LRU, near ARC)"
    elif diff_lru > 0:
        status += " (Beats LRU & FIFO)"
        
    print(f"C = {c:<8} {lfu:6.2f}%    {fifo:6.2f}%    {lru:6.2f}%    {arc:6.2f}%    {anf:6.2f}%         {diff_lru:+6.2f}%      {diff_arc:+6.2f}%      {status}")

# 2. From cache_results_results.csv (Capacities 32 to 512)
with open("cache_results_results.csv", "r") as f:
    rows = list(csv.DictReader(f))

std_caps = ["32", "64", "128", "256", "512"]
std_pols = ["LFU", "FIFO", "LRU", "ARC", "FastLutAnfis"]
target_wls = ["Scan_Dominated (Sequential)", "zipfian", "phase_shift"]

data_std = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
for r in rows:
    wl = r["workload"]
    c = r["capacity"]
    p = r["policy"]
    if wl in target_wls and p in std_pols:
        data_std[wl][c][p].append(float(r["hit_rate_pct"]))

print("\n" + "=" * 115)
print(" 3-WAY AVERAGE: SCAN-DOMINATED + ZIPFIAN + PHASE-SHIFTING (Large Capacities C = 32 to 512)")
print("=" * 115)
print(f"{'Capacity (C)':<14} {'LFU':<10} {'FIFO':<10} {'LRU':<10} {'ARC':<10} {'Fast-LUT ANFIS':<16} {'vs LRU':<12} {'vs ARC':<12} {'Rank / Status'}")
print("-" * 115)

for c in std_caps:
    means = {}
    for p in std_pols:
        s = 0.0
        for wl in target_wls:
            arr = data_std[wl][c][p]
            s += sum(arr) / len(arr)
        means[p] = s / len(target_wls)
        
    anf = means["FastLutAnfis"]
    lru = means["LRU"]
    arc = means["ARC"]
    fifo = means["FIFO"]
    lfu = means["LFU"]
    
    diff_lru = anf - lru
    diff_arc = anf - arc
    
    all_scores = [("ANFIS", anf), ("LRU", lru), ("ARC", arc), ("FIFO", fifo), ("LFU", lfu)]
    all_scores.sort(key=lambda x: x[1], reverse=True)
    rank = [x[0] for x in all_scores].index("ANFIS") + 1
    
    status = f"Rank #{rank}"
    if rank == 1:
        status += " (BETTER THAN ALL!)"
    elif diff_lru > 0 and abs(diff_arc) < 1.0:
        status += " (Beats LRU, near ARC)"
    elif diff_lru > 0:
        status += " (Beats LRU & FIFO)"
        
    print(f"C = {c:<8} {lfu:6.2f}%    {fifo:6.2f}%    {lru:6.2f}%    {arc:6.2f}%    {anf:6.2f}%         {diff_lru:+6.2f}%      {diff_arc:+6.2f}%      {status}")
