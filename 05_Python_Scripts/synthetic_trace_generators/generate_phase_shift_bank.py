import os
import csv
import numpy as np

def generate_phase_shift_trace(archetype: str, target_c: int, n_requests: int = 25000, seed: int = 42):
    rng = np.random.default_rng(seed)
    universe_size = max(1000, int(target_c * rng.uniform(20, 50)))
    hot_size = max(15, int(target_c * rng.uniform(0.6, 1.5)))
    
    stream = np.empty(n_requests, dtype=np.uint64)
    num_phases = rng.integers(4, 11)
    phase_len = n_requests // num_phases
    
    if archetype == "abrupt_hop_phases":
        # Hot working set abruptly hops to a new disjoint region every phase
        for p in range(num_phases):
            start = p * phase_len
            end = n_requests if p == num_phases - 1 else (p + 1) * phase_len
            p_len = end - start
            
            hot_base = rng.integers(0, max(1, universe_size - hot_size))
            hot_keys = np.arange(hot_base, hot_base + hot_size, dtype=np.uint64)
            
            # 85% inside the current hot set, 15% uniform cold background
            coin = rng.random(p_len)
            mask_hot = coin < 0.85
            mask_cold = ~mask_hot
            
            sub = np.empty(p_len, dtype=np.uint64)
            sub[mask_hot] = rng.choice(hot_keys, size=int(np.sum(mask_hot)))
            sub[mask_cold] = rng.integers(0, universe_size, size=int(np.sum(mask_cold)), dtype=np.uint64)
            stream[start:end] = sub

    elif archetype == "skew_migration_phases":
        # Distribution transitions between sharp Zipfian and uniform diffuse
        alphas = [1.35, 0.45, 1.20, 0.50, 1.10, 0.60]
        for p in range(num_phases):
            start = p * phase_len
            end = n_requests if p == num_phases - 1 else (p + 1) * phase_len
            p_len = end - start
            alpha = alphas[p % len(alphas)]
            
            ranks = np.arange(1, universe_size + 1, dtype=np.float64)
            weights = 1.0 / np.power(ranks, alpha)
            cdf = np.cumsum(weights)
            cdf /= cdf[-1]
            
            u = rng.random(p_len)
            stream[start:end] = np.searchsorted(cdf, u).astype(np.uint64)

    elif archetype == "multi_tenant_interleaved_phases":
        # Rapid switching between Tenant A (low addresses) and Tenant B (high addresses)
        tenant_chunk = rng.integers(500, 1500)
        curr_tenant = 0
        for i in range(0, n_requests, tenant_chunk):
            end = min(n_requests, i + tenant_chunk)
            p_len = end - i
            if curr_tenant == 0:
                base = 0
                keys = np.arange(base, base + hot_size, dtype=np.uint64)
            else:
                base = universe_size // 2
                keys = np.arange(base, base + hot_size, dtype=np.uint64)
                
            coin = rng.random(p_len)
            mask_hot = coin < 0.80
            mask_cold = ~mask_hot
            sub = np.empty(p_len, dtype=np.uint64)
            sub[mask_hot] = rng.choice(keys, size=int(np.sum(mask_hot)))
            sub[mask_cold] = rng.integers(0, universe_size, size=int(np.sum(mask_cold)), dtype=np.uint64)
            stream[i:end] = sub
            curr_tenant = 1 - curr_tenant

    elif archetype == "gradual_drift_phases":
        # Hot center drifts slowly across memory space
        drift_step = max(1, universe_size // 30)
        curr_center = 0
        for p in range(num_phases):
            start = p * phase_len
            end = n_requests if p == num_phases - 1 else (p + 1) * phase_len
            p_len = end - start
            
            hot_base = curr_center % max(1, universe_size - hot_size)
            hot_keys = np.arange(hot_base, hot_base + hot_size, dtype=np.uint64)
            
            coin = rng.random(p_len)
            mask_hot = coin < 0.85
            mask_cold = ~mask_hot
            sub = np.empty(p_len, dtype=np.uint64)
            sub[mask_hot] = rng.choice(hot_keys, size=int(np.sum(mask_hot)))
            sub[mask_cold] = rng.integers(0, universe_size, size=int(np.sum(mask_cold)), dtype=np.uint64)
            stream[start:end] = sub
            curr_center += drift_step

    elif archetype == "bursty_phase_spikes":
        # Base hot set interrupted by periodic massive cold bursts
        base_keys = np.arange(0, hot_size, dtype=np.uint64)
        for p in range(num_phases):
            start = p * phase_len
            end = n_requests if p == num_phases - 1 else (p + 1) * phase_len
            p_len = end - start
            
            if (p % 2) == 1:
                # Cold burst phase: access 3x hot_size unrepeated blocks
                burst_base = 50000 + p * 10000
                stream[start:end] = rng.integers(burst_base, burst_base + hot_size * 4, size=p_len, dtype=np.uint64)
            else:
                # Normal warm phase
                coin = rng.random(p_len)
                mask_hot = coin < 0.90
                mask_cold = ~mask_hot
                sub = np.empty(p_len, dtype=np.uint64)
                sub[mask_hot] = rng.choice(base_keys, size=int(np.sum(mask_hot)))
                sub[mask_cold] = rng.integers(0, universe_size, size=int(np.sum(mask_cold)), dtype=np.uint64)
                stream[start:end] = sub
    else:
        stream = rng.integers(0, universe_size, size=n_requests, dtype=np.uint64)

    unique_count = len(np.unique(stream))
    return stream, num_phases, hot_size, unique_count

def generate_phase_shift_bank(num_files: int = 1000, n_requests: int = 25000):
    base_dir = os.path.join("cpp", "traces", "phase_shift_bank")
    os.makedirs(base_dir, exist_ok=True)
    manifest_path = os.path.join(base_dir, "phase_shift_manifest.csv")
    
    capacities = [32, 64, 128, 256, 512]
    archetypes = [
        "abrupt_hop_phases",
        "skew_migration_phases",
        "multi_tenant_interleaved_phases",
        "gradual_drift_phases",
        "bursty_phase_spikes"
    ]
    
    print(f"Generating {num_files} Dynamic Phase-Shifting trace files (25,000 requests each)...")
    print(f"Output directory: {base_dir}")
    
    manifest_rows = []
    files_per_cap = num_files // len(capacities)
    file_idx = 1
    
    for cap in capacities:
        for f in range(files_per_cap):
            arch = archetypes[f % len(archetypes)]
            seed = 300000 + file_idx * 103
            
            stream, num_phases, hot_size, unique_blocks = generate_phase_shift_trace(
                archetype=arch, target_c=cap, n_requests=n_requests, seed=seed
            )
            
            fname = f"phase_shift_{file_idx:04d}.trace"
            fpath = os.path.join(base_dir, fname)
            
            np.savetxt(fpath, stream, fmt="%u")
            
            manifest_rows.append({
                "trace_id": file_idx,
                "filename": fname,
                "target_capacity": cap,
                "archetype": arch,
                "num_phases": num_phases,
                "hot_size": hot_size,
                "total_requests": n_requests,
                "unique_blocks": unique_blocks
            })
            
            if file_idx % 100 == 0 or file_idx == num_files:
                print(f"  Generated {file_idx}/{num_files} Phase-Shift trace files...", end="\r", flush=True)
            file_idx += 1
            
    with open(manifest_path, "w", newline="") as mf:
        fieldnames = ["trace_id", "filename", "target_capacity", "archetype", "num_phases", "hot_size", "total_requests", "unique_blocks"]
        writer = csv.DictWriter(mf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)
        
    print(f"\nPhase-shift bank generation complete! Manifest written to {manifest_path}")

if __name__ == "__main__":
    generate_phase_shift_bank(num_files=1000, n_requests=25000)
