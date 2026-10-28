import urllib.request
import ssl

ctx = ssl._create_unverified_context()
url = "https://ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/cacheDatasets/msr/"

req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, context=ctx) as resp:
    print(resp.read()[:1500].decode())
