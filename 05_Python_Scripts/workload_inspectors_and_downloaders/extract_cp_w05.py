import os
import sys
import struct
import urllib.request
import ssl
import zstandard as zstd

DEST_DIR = r"c:\Users\Asus\OneDrive\Desktop\Soft computing Project\new ideas\Optimized Standard ANFIS\cpp\traces"
OUT_TRACE = os.path.join(DEST_DIR, "cloudphysics_w05.trace")
URL = "https://ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/cacheDatasets/cloudphysics/w05.oracleGeneral.bin.zst"

ctx = ssl._create_unverified_context()

def stream_and_extract(max_requests=50000):
    print(f"Streaming and extracting {max_requests} requests from CloudPhysics trace w05...")
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    dctx = zstd.ZstdDecompressor()
    decompressor = dctx.decompressobj()
    
    RECORD_SIZE = 24
    RECORD_FORMAT = "<IQIq"
    blocks = []
    uncompressed_buf = bytearray()
    bytes_downloaded = 0
    
    with urllib.request.urlopen(req, context=ctx) as resp:
        while len(blocks) < max_requests:
            chunk = resp.read(32768)
            if not chunk:
                break
            bytes_downloaded += len(chunk)
            
            try:
                decompressed = decompressor.decompress(chunk)
            except Exception as e:
                print("Decomp error:", e)
                break
                
            if decompressed:
                uncompressed_buf.extend(decompressed)
                
            while len(uncompressed_buf) >= RECORD_SIZE and len(blocks) < max_requests:
                rec_bytes = bytes(uncompressed_buf[:RECORD_SIZE])
                del uncompressed_buf[:RECORD_SIZE]
                ts, obj_id, size, next_vtime = struct.unpack(RECORD_FORMAT, rec_bytes)
                page_id = obj_id // 4096
                blocks.append(page_id)
                
            sys.stdout.write(f"\r  Downloaded: {bytes_downloaded / 1024:.1f} KB | Extracted: {len(blocks)} / {max_requests} blocks")
            sys.stdout.flush()
            
    print(f"\nExtracted {len(blocks)} requests. Unique 4KB pages: {len(set(blocks))}")
    with open(OUT_TRACE, "w") as f_out:
        for b in blocks:
            f_out.write(f"{b}\n")
    print(f"Saved: {OUT_TRACE}")

if __name__ == "__main__":
    stream_and_extract(50000)
