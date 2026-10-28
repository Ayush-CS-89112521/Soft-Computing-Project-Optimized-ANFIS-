import urllib.request
import json
import os

target_dir = r"c:\Users\Asus\OneDrive\Desktop\Soft computing Project\new ideas\Optimized Standard ANFIS"
# Search github code for sn-jnl.cls filename
url = "https://api.github.com/search/code?q=filename:sn-jnl.cls"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        items = data.get("items", [])
        if items:
            raw_url = items[0]["html_url"].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            print(f"Found sn-jnl.cls at {raw_url}")
            f_req = urllib.request.Request(raw_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(f_req, timeout=15) as f_resp:
                content = f_resp.read()
                with open(os.path.join(target_dir, "sn-jnl.cls"), "wb") as out_f:
                    out_f.write(content)
                print(f"Saved sn-jnl.cls ({len(content)} bytes)")
        else:
            print("No items found.")
except Exception as e:
    print("Search error:", e)
