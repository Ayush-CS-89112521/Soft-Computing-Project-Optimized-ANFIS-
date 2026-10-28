import urllib.request
import ssl

ctx = ssl._create_unverified_context()

urls = [
    ("WebSearch1", "http://skuld.cs.umass.edu/traces/storage/WebSearch1.spc.bz2"),
    ("Financial1", "http://skuld.cs.umass.edu/traces/storage/Financial1.spc.bz2"),
    ("Financial2", "http://skuld.cs.umass.edu/traces/storage/Financial2.spc.bz2"),
    ("WebSearch2", "http://skuld.cs.umass.edu/traces/storage/WebSearch2.spc.bz2")
]

for name, url in urls:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            print(f"{name}: SUCCESS! Content-Length: {resp.headers.get('Content-Length')} bytes")
    except Exception as e:
        print(f"{name}: FAILED: {e}")
