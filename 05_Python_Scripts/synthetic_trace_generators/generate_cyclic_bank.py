import os
import csv
import random
import numpy as np

def generate_cyclic_trace(archetype: str, target_c: int, n_requests: int = 25000, seed: int = 42):
    rng = np.random.default_rng(seed)
    
    # Loop length scaled relative to target capacity
    # Critical thrashing zone is around 1.05x to 1.3x capacity
    ratio = rng.uniform(0.7, 1.4)
    L = max(10, int(target_c * ratio))
    
    noise_pct = 0.0
    
    if archetype == "pure_cyclic":
        pattern = np.arange(L, dtype=np.uint64)
        repeats = (n_requests // L) + 1
        stream = np.tile(pattern, repeats)[:n_requests]
        
    elif archetype == "noisy_cyclic":
        noise_pct = rng.uniform(0.02, 0.15)
        pattern = np.arange(L, dtype=np.uint64)
        repeats = (n_requests // L) + 1
        base_stream = np.tile(pattern, repeats)[:n_requests]
        
        # Inject random noise blocks
        noise_mask = rng.random(n_requests) < noise_pct
        num_noise = int(np.sum(noise_mask))
        if num_noise > 0:
            noise_keys = rng.integers(100000, 200000, size=num_noise, dtype=np.uint64)
            base_stream[noise_mask] = noise_keys
        stream = base_stream
        
    elif archetype == "bidirectional":
        # Ping-pong loop: 0 ... L-1 ... 1
        pattern = np.concatenate([np.arange(L, dtype=np.uint64), np.arange(L - 2, 0, -1, dtype=np.uint64)])
        repeats = (n_requests // len(pattern)) + 1
        stream = np.tile(pattern, repeats)[:n_requests]
        
    elif archetype == "interleaved_dual":
        # Two loops: inner loop L1 and outer loop L2
        L1 = max(5, int(L * 0.4))
        L2 = max(10, L)
        pattern1 = np.arange(L1, dtype=np.uint64)
        pattern2 = np.arange(1000, 1000 + L2, dtype=np.uint64)
        
        stream = np.empty(n_requests, dtype=np.uint64)
        idx1 = 0
        idx2 = 0
        for i in range(n_requests):
            if (i % 3) == 0:
                stream[i] = pattern1[idx1 % L1]
                idx1 += 1
            else:
                stream[i] = pattern2[idx2 % L2]
                idx2 += 1
                
    elif archetype == "phase_cyclic":
        # Base offset shifts every 5000 requests
        phase_len = 5000
        stream = np.empty(n_requests, dtype=np.uint64)
        for phase in range(0, n_requests, phase_len):
            end = min(n_requests, phase + phase_len)
            base_offset = phase * 10
            p_len = end - phase
            pattern = np.arange(base_offset, base_offset + L, dtype=np.uint64)
            repeats = (p_len // L) + 1
            stream[phase:end] = np.tile(pattern, repeats)[:p_len]
            
    else:
        pattern = np.arange(L, dtype=np.uint64)
        repeats = (n_requests // L) + 1
        stream = np.tile(pattern, repeats)[:n_requests]

    unique_count = len(np.unique(stream))
    return stream, L, noise_pct, unique_count

def generate_bank(num_files: int = 1000, n_requests: int = 25000):
    base_dir = os.path.join("cpp", "traces", "cyclic_bank")
    os.makedirs(base_dir, exist_ok=True)
    
    manifest_path = os.path.join(base_dir, "cyclic_manifest.csv")
    
    capacities = [32, 64, 128, 256, 512]
    archetypes = ["pure_cyclic", "noisy_cyclic", "bidirectional", "interleaved_dual", "phase_cyclic"]
    
    print(f"Generating {num_files} cyclic trace files (25,000 requests each)...")
    print(f"Output directory: {base_dir}")
    
    manifest_rows = []
    
    files_per_cap = num_files // len(capacities)
    file_idx = 1
    
    for cap in capacities:
        for f in range(files_per_cap):
            arch = archetypes[f % len(archetypes)]
            seed = 100000 + file_idx * 73
            
            stream, loop_len, noise_pct, unique_blocks = generate_cyclic_trace(
                archetype=arch, target_c=cap, n_requests=n_requests, seed=seed
            )
            
            fname = f"cyclic_trace_{file_idx:04d}.trace"
            fpath = os.path.join(base_dir, fname)
            
            # Fast text write
            np.savetxt(fpath, stream, fmt="%u")
            
            manifest_rows.append({
                "trace_id": file_idx,
                "filename": fname,
                "target_capacity": cap,
                "archetype": arch,
                "loop_length": loop_len,
                "noise_pct": round(noise_pct * 100, 2),
                "total_requests": n_requests,
                "unique_blocks": unique_blocks
            })
            
            if file_idx % 100 == 0 or file_idx == num_files:
                print(f"  Generated {file_idx}/{num_files} trace files...", end="\r", flush=True)
            file_idx += 1
            
    with open(manifest_path, "w", newline="") as mf:
        fieldnames = ["trace_id", "filename", "target_capacity", "archetype", "loop_length", "noise_pct", "total_requests", "unique_blocks"]
        writer = csv.DictWriter(mf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)
        
    print(f"\nBank generation complete! Manifest written to {manifest_path}")

if __name__ == "__main__":
    generate_bank(num_files=1000, n_requests=25000)
