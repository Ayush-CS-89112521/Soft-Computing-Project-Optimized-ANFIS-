import urllib.request
import re
import ssl

ctx = ssl._create_unverified_context()
url = "https://ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/cacheDatasets/msr/"

req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        files = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html)
        print("Total items:", len(files))
        for f in files[:25]:
            if "msr" in f or "zst" in f or "csv" in f or "trace" in f:
                print("  ", f)
except Exception as e:
    print("Error:", e)
