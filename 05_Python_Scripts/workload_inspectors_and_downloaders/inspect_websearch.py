trace_path = r"c:\Users\Asus\OneDrive\Desktop\Soft computing Project\new ideas\Optimized Standard ANFIS\cpp\traces\umass_websearch1.trace"
with open(trace_path) as f:
    lines = [int(line.strip()) for line in f if line.strip()]

print("Total requests:", len(lines))
print("Unique blocks:", len(set(lines)))
print("Min block:", min(lines), "Max block:", max(lines))

# Check block sizes: WebSearch LBNs are often byte offsets or 512-byte sectors!
# In WebSearch.spc, column 1 is BlockNumber (offset in bytes or sectors).
# In UMass WebSearch, BlockNumber is byte offset: dividing by 4096 (4KB page) or 512 (sector) is standard!
sectors = [x // 512 for x in lines]
pages = [x // 4096 for x in lines]
print("Unique 512-byte sectors:", len(set(sectors)))
print("Unique 4KB pages:", len(set(pages)))
