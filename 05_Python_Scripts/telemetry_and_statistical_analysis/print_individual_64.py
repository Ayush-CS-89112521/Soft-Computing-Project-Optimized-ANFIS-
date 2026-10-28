import csv
from collections import defaultdict

with open("cache_results_results.csv", "r") as f:
    rows = [r for r in csv.DictReader(f) if r["capacity"] == "64"]

policies = ["LFU", "FIFO", "LRU", "ARC", "FastLutAnfis"]
wl_data = defaultdict(lambda: defaultdict(list))

for r in rows:
    wl = r["workload"]
    p = r["policy"]
    if p in policies:
        wl_data[wl][p].append({
            "hr": float(r["hit_rate_pct"]),
            "reqs": int(r["accesses"]),
            "hits": int(r["hits"]),
            "misses": int(r["misses"]),
            "lat": float(r["avg_latency_ns"])
        })

print("=" * 115)
print(f"{'Workload Name':<32} {'Requests':<10} {'Fast-LUT ANFIS':<18} {'IBM ARC':<12} {'Classical LRU':<15} {'FIFO':<10} {'LFU':<10}")
print("=" * 115)

for wl, p_dict in wl_data.items():
    anf_list = p_dict["FastLutAnfis"]
    lru_list = p_dict["LRU"]
    arc_list = p_dict["ARC"]
    fifo_list = p_dict["FIFO"]
    lfu_list = p_dict["LFU"]
    
    total_reqs = sum(x["reqs"] for x in anf_list)
    anf_hr = sum(x["hr"] for x in anf_list) / len(anf_list)
    lru_hr = sum(x["hr"] for x in lru_list) / len(lru_list)
    arc_hr = sum(x["hr"] for x in arc_list) / len(arc_list)
    fifo_hr = sum(x["hr"] for x in fifo_list) / len(fifo_list)
    lfu_hr = sum(x["hr"] for x in lfu_list) / len(lfu_list)
    
    anf_hits = sum(x["hits"] for x in anf_list)
    anf_lat = sum(x["lat"] for x in anf_list) / len(anf_list)
    
    anf_str = f"{anf_hr:5.2f}% ({anf_lat:4.1f}ns)"
    print(f"{wl:<32} {total_reqs:<10} {anf_str:<18} {arc_hr:5.2f}%{'':<5} {lru_hr:5.2f}%{'':<8} {fifo_hr:5.2f}%{'':<4} {lfu_hr:5.2f}%")
