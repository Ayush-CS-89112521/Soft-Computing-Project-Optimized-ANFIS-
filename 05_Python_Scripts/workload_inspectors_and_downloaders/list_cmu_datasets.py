import urllib.request
import re
import ssl

ctx = ssl._create_unverified_context()
url = "https://ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/cacheDatasets/"

req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        files = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html)
        print("Datasets available:")
        for f in files:
            print("  ", f)
except Exception as e:
    print("Error:", e)
