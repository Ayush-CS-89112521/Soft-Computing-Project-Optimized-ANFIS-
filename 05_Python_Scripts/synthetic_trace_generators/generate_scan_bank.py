import os
import csv
import numpy as np

def generate_scan_trace(archetype: str, target_c: int, n_requests: int = 25000, seed: int = 42):
    rng = np.random.default_rng(seed)
    hot_size = max(10, int(target_c * rng.uniform(0.5, 0.95))) # fits inside or near cache
    hot_keys = np.arange(0, hot_size, dtype=np.uint64)
    
    stream = np.empty(n_requests, dtype=np.uint64)
    
    if archetype == "interleaved_hot_scan":
        # Hot set interleaved with sequential scan stream
        scan_ratio = rng.uniform(0.15, 0.40)
        coin = rng.random(n_requests)
        mask_scan = coin < scan_ratio
        mask_hot = ~mask_scan
        
        num_scans = int(np.sum(mask_scan))
        scan_keys = np.arange(100000, 100000 + num_scans, dtype=np.uint64)
        
        stream[mask_hot] = rng.choice(hot_keys, size=int(np.sum(mask_hot)))
        stream[mask_scan] = scan_keys

    elif archetype == "periodic_large_burst_scan":
        # Normal high-locality access interrupted by large sequential sweeps of size 3x-8x C
        burst_interval = rng.integers(3000, 6000)
        curr_idx = 0
        scan_block_counter = 200000
        
        while curr_idx < n_requests:
            chunk_len = min(n_requests - curr_idx, burst_interval)
            # 80% of chunk is warm hot set
            warm_len = int(chunk_len * 0.75)
            burst_len = chunk_len - warm_len
            
            stream[curr_idx:curr_idx + warm_len] = rng.choice(hot_keys, size=warm_len)
            curr_idx += warm_len
            
            if burst_len > 0:
                stream[curr_idx:curr_idx + burst_len] = np.arange(scan_block_counter, scan_block_counter + burst_len, dtype=np.uint64)
                scan_block_counter += burst_len
                curr_idx += burst_len

    elif archetype == "multi_stride_scan":
        # Strided sequential access (stride 1, 2, or 4) mixed with hot lookups
        stride = rng.choice([1, 2, 4])
        scan_ratio = rng.uniform(0.20, 0.35)
        coin = rng.random(n_requests)
        mask_scan = coin < scan_ratio
        mask_hot = ~mask_scan
        
        num_scans = int(np.sum(mask_scan))
        scan_keys = np.arange(300000, 300000 + num_scans * stride, stride, dtype=np.uint64)[:num_scans]
        
        stream[mask_hot] = rng.choice(hot_keys, size=int(np.sum(mask_hot)))
        stream[mask_scan] = scan_keys

    elif archetype == "segmented_scans":
        # Multiple independent short scans of length 40-100 blocks
        curr_idx = 0
        scan_base = 400000
        while curr_idx < n_requests:
            if rng.random() < 0.70:
                warm_step = min(n_requests - curr_idx, rng.integers(200, 500))
                stream[curr_idx:curr_idx + warm_step] = rng.choice(hot_keys, size=warm_step)
                curr_idx += warm_step
            else:
                scan_step = min(n_requests - curr_idx, rng.integers(40, 120))
                stream[curr_idx:curr_idx + scan_step] = np.arange(scan_base, scan_base + scan_step, dtype=np.uint64)
                scan_base += scan_step
                curr_idx += scan_step

    elif archetype == "heavy_scan_pressure":
        # 60% scan pressure (severe cache wash test)
        scan_ratio = rng.uniform(0.50, 0.70)
        coin = rng.random(n_requests)
        mask_scan = coin < scan_ratio
        mask_hot = ~mask_scan
        
        num_scans = int(np.sum(mask_scan))
        scan_keys = np.arange(500000, 500000 + num_scans, dtype=np.uint64)
        
        stream[mask_hot] = rng.choice(hot_keys, size=int(np.sum(mask_hot)))
        stream[mask_scan] = scan_keys
    else:
        stream = rng.choice(hot_keys, size=n_requests)

    unique_count = len(np.unique(stream))
    scan_pct = round(float(np.sum(stream >= 100000)) / n_requests * 100, 2)
    return stream, hot_size, scan_pct, unique_count

def generate_scan_bank(num_files: int = 1000, n_requests: int = 25000):
    base_dir = os.path.join("cpp", "traces", "scan_bank")
    os.makedirs(base_dir, exist_ok=True)
    manifest_path = os.path.join(base_dir, "scan_manifest.csv")
    
    capacities = [32, 64, 128, 256, 512]
    archetypes = [
        "interleaved_hot_scan",
        "periodic_large_burst_scan",
        "multi_stride_scan",
        "segmented_scans",
        "heavy_scan_pressure"
    ]
    
    print(f"Generating {num_files} Scan-Dominated trace files (25,000 requests each)...")
    print(f"Output directory: {base_dir}")
    
    manifest_rows = []
    files_per_cap = num_files // len(capacities)
    file_idx = 1
    
    for cap in capacities:
        for f in range(files_per_cap):
            arch = archetypes[f % len(archetypes)]
            seed = 400000 + file_idx * 107
            
            stream, hot_size, scan_pct, unique_blocks = generate_scan_trace(
                archetype=arch, target_c=cap, n_requests=n_requests, seed=seed
            )
            
            fname = f"scan_{file_idx:04d}.trace"
            fpath = os.path.join(base_dir, fname)
            
            np.savetxt(fpath, stream, fmt="%u")
            
            manifest_rows.append({
                "trace_id": file_idx,
                "filename": fname,
                "target_capacity": cap,
                "archetype": arch,
                "hot_size": hot_size,
                "scan_pct": scan_pct,
                "total_requests": n_requests,
                "unique_blocks": unique_blocks
            })
            
            if file_idx % 100 == 0 or file_idx == num_files:
                print(f"  Generated {file_idx}/{num_files} Scan-Dominated trace files...", end="\r", flush=True)
            file_idx += 1
            
    with open(manifest_path, "w", newline="") as mf:
        fieldnames = ["trace_id", "filename", "target_capacity", "archetype", "hot_size", "scan_pct", "total_requests", "unique_blocks"]
        writer = csv.DictWriter(mf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)
        
    print(f"\nScan bank generation complete! Manifest written to {manifest_path}")

if __name__ == "__main__":
    generate_scan_bank(num_files=1000, n_requests=25000)
