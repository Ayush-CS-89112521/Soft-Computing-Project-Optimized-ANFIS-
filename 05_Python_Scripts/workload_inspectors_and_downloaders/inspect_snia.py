with open(r"c:\Users\Asus\OneDrive\Desktop\Soft computing Project\new ideas\Optimized Standard ANFIS\cpp\traces\snia_msr_hm0.trace") as f:
    blocks = [int(line.strip()) for line in f if line.strip()]

print("Total blocks:", len(blocks))
print("Unique raw:", len(set(blocks)))
pages = [b // 4096 for b in blocks]
print("Unique 4KB pages:", len(set(pages)))
sectors = [b // 512 for b in blocks]
print("Unique 512-byte sectors:", len(set(sectors)))
