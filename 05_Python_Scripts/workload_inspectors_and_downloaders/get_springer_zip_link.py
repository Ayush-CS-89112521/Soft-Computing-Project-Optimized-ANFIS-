import urllib.request
import re

url = "https://www.springernature.com/gp/authors/campaigns/latex-author-support"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        links = re.findall(r'href="([^"]+)"', html)
        candidate_links = [l for l in links if "template" in l.lower() or "latex" in l.lower() or "download" in l.lower()]
        print("Candidate links:", candidate_links[:10])
except Exception as e:
    print("Error:", e)
