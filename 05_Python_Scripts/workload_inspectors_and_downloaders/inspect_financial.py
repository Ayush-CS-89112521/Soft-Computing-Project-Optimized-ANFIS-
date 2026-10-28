trace_path = r"c:\Users\Asus\OneDrive\Desktop\Soft computing Project\new ideas\Optimized Standard ANFIS\cpp\traces\umass_financial1.trace"
with open(trace_path) as f:
    lines = [int(line.strip()) for line in f if line.strip()]

print("Financial1 Total requests:", len(lines))
print("Financial1 Unique raw:", len(set(lines)))
print("Min block:", min(lines), "Max block:", max(lines))

# Check Financial1 raw:
# In Financial1.spc, Column 1 is 512-byte block number (sector number).
# Let's check page numbers (// 8 for 4KB page)
pages = [x // 8 for x in lines]
print("Financial1 Unique 4KB pages (// 8):", len(set(pages)))
