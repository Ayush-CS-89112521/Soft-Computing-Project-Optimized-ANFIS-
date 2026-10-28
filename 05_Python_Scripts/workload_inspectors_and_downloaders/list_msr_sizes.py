import urllib.request
import re
import ssl

ctx = ssl._create_unverified_context()
url = "https://ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/cacheDatasets/msr/"

req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, context=ctx) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# Extract filename and size
rows = re.findall(r'<a href="([^"]+)">[^<]+</a>\s+([0-9A-Za-z-:\s]+)\s+([0-9.]+[KMG]?)', html)
for f, date, size in rows:
    if "msr" in f:
        print(f"{f:30} : {size}")
