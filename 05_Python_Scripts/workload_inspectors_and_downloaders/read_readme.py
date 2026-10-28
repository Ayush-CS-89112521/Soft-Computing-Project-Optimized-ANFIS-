import urllib.request
import ssl

ctx = ssl._create_unverified_context()
url = "https://ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/cacheDatasets/README"

req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        print(resp.read().decode('utf-8', errors='ignore'))
except Exception as e:
    print("Error:", e)
