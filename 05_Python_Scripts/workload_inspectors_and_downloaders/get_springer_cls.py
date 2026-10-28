import urllib.request
import json
import os

target_dir = r"c:\Users\Asus\OneDrive\Desktop\Soft computing Project\new ideas\Optimized Standard ANFIS"
url = "https://api.github.com/repos/hegyhati/Springer_journal_article_template/contents"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        print("Files in repo:", [x["name"] for x in data])
        for x in data:
            name = x["name"]
            if name == "sn-jnl.cls" or name.endswith(".bst"):
                durl = x["download_url"]
                print(f"Downloading {name} from {durl}...")
                f_req = urllib.request.Request(durl, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(f_req, timeout=15) as f_resp:
                    content = f_resp.read()
                    with open(os.path.join(target_dir, name), "wb") as out_f:
                        out_f.write(content)
                    print(f"Saved {name} ({len(content)} bytes)")
except Exception as e:
    print("Error:", e)
