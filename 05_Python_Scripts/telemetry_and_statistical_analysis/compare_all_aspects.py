import csv
from collections import defaultdict

# 1. Load results from cache_results_results.csv (covering C = 32, 64, 128, 256, 512)
with open("cache_results_results.csv", "r") as f:
    rows = list(csv.DictReader(f))

# Group by (workload, capacity, policy)
hr_data = defaultdict(lambda: defaultdict(list))
lat_data = defaultdict(lambda: defaultdict(list))

for r in rows:
    wl = r["workload"]
    c = r["capacity"]
    p = r["policy"]
    hr = float(r["hit_rate_pct"])
    lat = float(r["avg_latency_ns"])
    hr_data[(wl, c)][p].append(hr)
    lat_data[(wl, c)][p].append(lat)

# Workload categories:
# 1. Cyclic (Cyclic_Loop stress & synthetic cyclic)
# 2. Zipfian (synthetic zipfian & UMass websearch)
# 3. Phase Shifting (synthetic phase_shift)
# 4. Scan Dominated (Scan_Dominated stress & synthetic scan)
# 5. Real Enterprise (UMass Financial & CloudPhysics w02)

capacities = ["32", "64", "128", "256", "512"]

print("=========================================================================================")
print(" COMPREHENSIVE PERFORMANCE PROFILE ACROSS ALL 5 ASPECTS & 5 CAPACITIES")
print("=========================================================================================\n")

categories = {
    "1. Cyclic Loop Thrashing": "Cyclic_Loop (Stress)",
    "2. Zipfian Locality": "zipfian",
    "3. Dynamic Phase-Shifting": "phase_shift",
    "4. Scan-Dominated Streaming": "Scan_Dominated (Sequential)",
    "5. Real Financial OLTP": "UMass_Financial1 (OLTP)",
    "6. Real CloudPhysics VMware": "CloudPhysics_w02 (FAST '15)"
}

policies = ["LRU", "FIFO", "LFU", "ARC", "FastLutAnfis"]

for cat_name, wl_key in categories.items():
    print(f"\n--- {cat_name} ---")
    header = f"{'Capacity (C)':<14}" + "".join([f"{p:>14}" for p in policies]) + f"{'ANFIS vs LRU':>16}" + f"{'ANFIS vs ARC':>16}"
    print(header)
    print("-" * len(header))
    
    for c in capacities:
        vals = {}
        for p in policies:
            arr = hr_data[(wl_key, c)][p]
            vals[p] = sum(arr) / len(arr) if arr else 0.0
            
        anf = vals["FastLutAnfis"]
        lru = vals["LRU"]
        arc = vals["ARC"]
        gain_lru = anf - lru
        gain_arc = anf - arc
        
        line = f"C = {c:<8}"
        for p in policies:
            line += f"{vals[p]:>13.2f}%"
        line += f"{gain_lru:>+15.2f}%"
        line += f"{gain_arc:>+15.2f}%"
        print(line)

print("\n=========================================================================================")
print(" OVERALL AVERAGE HIT RATE ACROSS ALL ASPECTS PER CAPACITY")
print("=========================================================================================")
header = f"{'Capacity (C)':<14}" + "".join([f"{p:>14}" for p in policies]) + f"{'ANFIS vs LRU':>16}" + f"{'ANFIS vs ARC':>16}"
print(header)
print("-" * len(header))

for c in capacities:
    cat_anf = []
    cat_lru = []
    cat_arc = []
    cat_fifo = []
    cat_lfu = []
    
    for cat_name, wl_key in categories.items():
        cat_anf.append(sum(hr_data[(wl_key, c)]["FastLutAnfis"]) / len(hr_data[(wl_key, c)]["FastLutAnfis"]))
        cat_lru.append(sum(hr_data[(wl_key, c)]["LRU"]) / len(hr_data[(wl_key, c)]["LRU"]))
        cat_arc.append(sum(hr_data[(wl_key, c)]["ARC"]) / len(hr_data[(wl_key, c)]["ARC"]))
        cat_fifo.append(sum(hr_data[(wl_key, c)]["FIFO"]) / len(hr_data[(wl_key, c)]["FIFO"]))
        cat_lfu.append(sum(hr_data[(wl_key, c)]["LFU"]) / len(hr_data[(wl_key, c)]["LFU"]))
        
    m_anf = sum(cat_anf) / len(cat_anf)
    m_lru = sum(cat_lru) / len(cat_lru)
    m_arc = sum(cat_arc) / len(cat_arc)
    m_fifo = sum(cat_fifo) / len(cat_fifo)
    m_lfu = sum(cat_lfu) / len(cat_lfu)
    
    print(f"C = {c:<8}{m_lru:>13.2f}%{m_fifo:>13.2f}%{m_lfu:>13.2f}%{m_arc:>13.2f}%{m_anf:>13.2f}%{m_anf - m_lru:>+15.2f}%{m_anf - m_arc:>+15.2f}%")
