import urllib.request
import ssl

ctx = ssl._create_unverified_context()

test_urls = [
    ("SNIA MSR 388", "http://iotta.snia.org/traces/388"),
    ("SNIA FIU 390", "http://iotta.snia.org/traces/390"),
    ("Camelab MSRC", "https://camelab.org/"),
    ("CMU PDL MSR proj", "https://ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/cacheDatasets/msr/msr_proj_0.oracleGeneral.zst"),
    ("GitHub MSR sample", "https://raw.githubusercontent.com/stonet2000/msr-cambridge-traces/master/README.md")
]

for name, url in test_urls:
    print(f"Testing {name} ({url})...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            print(f"  SUCCESS! Code: {resp.status}, Content-Length: {resp.headers.get('Content-Length')}")
    except Exception as e:
        print(f"  FAILED: {e}")
