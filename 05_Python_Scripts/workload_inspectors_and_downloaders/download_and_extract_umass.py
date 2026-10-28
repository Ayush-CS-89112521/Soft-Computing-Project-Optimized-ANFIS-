import os
import urllib.request
import ssl
import bz2
import sys

DEST_DIR = r"c:\Users\Asus\OneDrive\Desktop\Soft computing Project\new ideas\Optimized Standard ANFIS\cpp\traces"
RAW_DIR = os.path.join(DEST_DIR, "umass_raw")
os.makedirs(RAW_DIR, exist_ok=True)

TRACES = [
    ("WebSearch1", "http://skuld.cs.umass.edu/traces/storage/WebSearch1.spc.bz2", "umass_websearch1.trace"),
    ("Financial1", "http://skuld.cs.umass.edu/traces/storage/Financial1.spc.bz2", "umass_financial1.trace")
]

ctx = ssl._create_unverified_context()

def download_and_process(name, url, output_trace_name, max_requests=50000):
    bz2_path = os.path.join(RAW_DIR, f"{name}.spc.bz2")
    out_path = os.path.join(DEST_DIR, output_trace_name)
    
    # 1. Download
    if not os.path.exists(bz2_path):
        print(f"Downloading {name} from {url}...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx) as resp, open(bz2_path, "wb") as f_out:
            total_size = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            block_size = 65536
            while True:
                chunk = resp.read(block_size)
                if not chunk:
                    break
                f_out.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    pct = (downloaded / total_size) * 100.0
                    sys.stdout.write(f"\r  Progress: {downloaded / 1024 / 1024:.2f} MB / {total_size / 1024 / 1024:.2f} MB ({pct:.1f}%)")
                    sys.stdout.flush()
        print(f"\n  Saved raw bz2 to: {bz2_path}")
    else:
        print(f"Raw archive {bz2_path} already exists, skipping download.")

    # 2. Decompress and parse ASCII LBN columns
    print(f"Parsing raw {name} trace: extracting LBN (BlockNumber)...")
    blocks = []
    
    with bz2.open(bz2_path, "rt", encoding="ascii", errors="ignore") as f:
        line_count = 0
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            # Formats in UMass SPC traces are typically comma-delimited:
            # ASU, BlockNumber, Size, Op, [Optional: Timestamp]
            parts = [p.strip() for p in line.replace(" ", ",").split(",") if p.strip()]
            if len(parts) >= 2:
                try:
                    # Column 1 is BlockNumber
                    raw_val = int(parts[1])
                    if "websearch" in name.lower():
                        # UMass WebSearch stores byte offsets; convert to 4KB OS page blocks (standard in cache papers)
                        block_num = raw_val // 4096
                    else:
                        # Financial1 stores 512-byte LBN sectors
                        block_num = raw_val
                    blocks.append(block_num)
                    line_count += 1
                    if max_requests > 0 and line_count >= max_requests:
                        break
                except ValueError:
                    continue

    print(f"Extracted {len(blocks)} requests from {name}.")
    
    # Write flat .trace file for C++ benchmark engine
    with open(out_path, "w") as f_out:
        for b in blocks:
            f_out.write(f"{b}\n")
            
    print(f"Written benchmark trace to: {out_path}\n")

if __name__ == "__main__":
    print("=== Starting Official UMass Repository Trace Downloader & Ingestion ===")
    for name, url, out_trace in TRACES:
        download_and_process(name, url, out_trace, max_requests=50000)
    print("All UMass traces downloaded and processed successfully!")
