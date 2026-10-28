import urllib.request
import ssl

ctx = ssl._create_unverified_context()
req = urllib.request.Request("http://iotta.snia.org/traces/388", headers={"User-Agent": "Mozilla/5.0"})

with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
    text = resp.read().decode('utf-8', errors='ignore')
    print("Page length:", len(text))
    print(text[:1000])
