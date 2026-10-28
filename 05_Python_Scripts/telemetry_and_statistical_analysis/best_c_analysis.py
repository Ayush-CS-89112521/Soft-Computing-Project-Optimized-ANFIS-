import csv

with open("cyclic_comparison_5policies.csv", "r") as f:
    rows = list(csv.DictReader(f))

print("=== Top Capacities with Highest Margin Over ARC & LRU in Cyclic ===")
sorted_rows = sorted(rows, key=lambda r: float(r["Gain_over_ARC_pct"]), reverse=True)
for r in sorted_rows[:7]:
    print(f"C = {r['capacity']:>2}: ANFIS = {r['FastLUT_ANFIS_hit_rate_pct']}%, ARC = {r['ARC_hit_rate_pct']}%, Gain vs ARC = {r['Gain_over_ARC_pct']}%, Gain vs LRU = {r['Gain_over_LRU_pct']}%")

print("\n=== Top Capacities with Highest Absolute Hit Rate ===")
sorted_abs = sorted(rows, key=lambda r: float(r["FastLUT_ANFIS_hit_rate_pct"]), reverse=True)
for r in sorted_abs[:7]:
    print(f"C = {r['capacity']:>2}: ANFIS = {r['FastLUT_ANFIS_hit_rate_pct']}%, ARC = {r['ARC_hit_rate_pct']}%, LRU = {r['LRU_hit_rate_pct']}%")
