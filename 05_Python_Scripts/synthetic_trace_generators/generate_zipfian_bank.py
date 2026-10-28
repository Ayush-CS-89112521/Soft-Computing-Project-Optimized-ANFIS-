import os
import csv
import numpy as np

def precompute_zipf_cdf(universe_size: int, alpha: float):
    ranks = np.arange(1, universe_size + 1, dtype=np.float64)
    weights = 1.0 / np.power(ranks, alpha)
    cdf = np.cumsum(weights)
    cdf /= cdf[-1]
    return cdf

def sample_zipf(cdf, n_samples: int, rng):
    u = rng.random(n_samples)
    return np.searchsorted(cdf, u).astype(np.uint64)

def generate_zipf_trace(archetype: str, target_c: int, n_requests: int = 25000, seed: int = 42):
    rng = np.random.default_rng(seed)
    
    # Universe size scaled with capacity (e.g., 10x to 40x cache size)
    universe_size = max(500, int(target_c * rng.uniform(15, 35)))
    alpha = rng.uniform(0.70, 1.25)
    
    if archetype == "stationary_zipf":
        cdf = precompute_zipf_cdf(universe_size, alpha)
        stream = sample_zipf(cdf, n_requests, rng)
        
    elif archetype == "shuffled_rank_zipf":
        # Rank ordering rotates every 5000 requests
        cdf = precompute_zipf_cdf(universe_size, alpha)
        phase_len = 5000
        stream = np.empty(n_requests, dtype=np.uint64)
        for phase in range(0, n_requests, phase_len):
            end = min(n_requests, phase + phase_len)
            p_len = end - phase
            raw_ranks = sample_zipf(cdf, p_len, rng)
            # Permutation for this phase
            perm = rng.permutation(universe_size).astype(np.uint64)
            stream[phase:end] = perm[raw_ranks]
            
    elif archetype == "zipf_with_scans":
        # 85% Zipfian requests, 15% sequential scan requests
        cdf = precompute_zipf_cdf(universe_size, alpha)
        stream = sample_zipf(cdf, n_requests, rng)
        scan_ratio = rng.uniform(0.08, 0.20)
        scan_mask = rng.random(n_requests) < scan_ratio
        num_scans = int(np.sum(scan_mask))
        if num_scans > 0:
            scan_keys = np.arange(500000, 500000 + num_scans, dtype=np.uint64)
            stream[scan_mask] = scan_keys
            
    elif archetype == "bimodal_zipf":
        # Two distinct Zipfian distributions (hot table A and cold table B)
        u1 = universe_size // 3
        u2 = universe_size - u1
        cdf1 = precompute_zipf_cdf(u1, alpha + 0.15)
        cdf2 = precompute_zipf_cdf(u2, max(0.5, alpha - 0.2))
        
        stream = np.empty(n_requests, dtype=np.uint64)
        coin = rng.random(n_requests)
        mask1 = coin < 0.75
        mask2 = ~mask1
        
        stream[mask1] = sample_zipf(cdf1, int(np.sum(mask1)), rng)
        stream[mask2] = u1 + sample_zipf(cdf2, int(np.sum(mask2)), rng)
        
    elif archetype == "varying_alpha_zipf":
        # Alpha changes from mild (0.65) to steep (1.30)
        stream = np.empty(n_requests, dtype=np.uint64)
        quarters = 4
        q_len = n_requests // quarters
        alphas = [0.70, 0.90, 1.10, 1.30]
        rng.shuffle(alphas)
        for q in range(quarters):
            start = q * q_len
            end = n_requests if q == quarters - 1 else (q + 1) * q_len
            sub_cdf = precompute_zipf_cdf(universe_size, alphas[q])
            stream[start:end] = sample_zipf(sub_cdf, end - start, rng)
    else:
        cdf = precompute_zipf_cdf(universe_size, alpha)
        stream = sample_zipf(cdf, n_requests, rng)

    unique_count = len(np.unique(stream))
    return stream, alpha, universe_size, unique_count

def generate_zipf_bank(num_files: int = 1000, n_requests: int = 25000):
    base_dir = os.path.join("cpp", "traces", "zipfian_bank")
    os.makedirs(base_dir, exist_ok=True)
    manifest_path = os.path.join(base_dir, "zipfian_manifest.csv")
    
    capacities = [32, 64, 128, 256, 512]
    archetypes = ["stationary_zipf", "shuffled_rank_zipf", "zipf_with_scans", "bimodal_zipf", "varying_alpha_zipf"]
    
    print(f"Generating {num_files} Zipfian locality trace files (25,000 requests each)...")
    print(f"Output directory: {base_dir}")
    
    manifest_rows = []
    files_per_cap = num_files // len(capacities)
    file_idx = 1
    
    for cap in capacities:
        for f in range(files_per_cap):
            arch = archetypes[f % len(archetypes)]
            seed = 200000 + file_idx * 97
            
            stream, alpha, universe_size, unique_blocks = generate_zipf_trace(
                archetype=arch, target_c=cap, n_requests=n_requests, seed=seed
            )
            
            fname = f"zipf_trace_{file_idx:04d}.trace"
            fpath = os.path.join(base_dir, fname)
            
            np.savetxt(fpath, stream, fmt="%u")
            
            manifest_rows.append({
                "trace_id": file_idx,
                "filename": fname,
                "target_capacity": cap,
                "archetype": arch,
                "alpha": round(alpha, 3),
                "universe_size": universe_size,
                "total_requests": n_requests,
                "unique_blocks": unique_blocks
            })
            
            if file_idx % 100 == 0 or file_idx == num_files:
                print(f"  Generated {file_idx}/{num_files} Zipfian trace files...", end="\r", flush=True)
            file_idx += 1
            
    with open(manifest_path, "w", newline="") as mf:
        fieldnames = ["trace_id", "filename", "target_capacity", "archetype", "alpha", "universe_size", "total_requests", "unique_blocks"]
        writer = csv.DictWriter(mf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)
        
    print(f"\nZipfian bank generation complete! Manifest written to {manifest_path}")

if __name__ == "__main__":
    generate_zipf_bank(num_files=1000, n_requests=25000)
