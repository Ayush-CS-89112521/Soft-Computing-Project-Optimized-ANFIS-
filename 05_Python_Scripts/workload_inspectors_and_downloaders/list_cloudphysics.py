import urllib.request
import re
import ssl

ctx = ssl._create_unverified_context()
url = "https://ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/cacheDatasets/cloudphysics/"

req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        files = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html)
        print("CloudPhysics files available:")
        for f in files:
            if "oracleGeneral" in f or "zst" in f or "vmdk" in f or "csv" in f:
                print("  ", f)
except Exception as e:
    print("Error:", e)
