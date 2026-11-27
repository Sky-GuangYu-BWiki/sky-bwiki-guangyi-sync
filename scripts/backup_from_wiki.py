import urllib.request
import urllib.parse
import json
import os
from datetime import datetime

PAGES = [
    ("复刻计时器", "src/pages/复刻计时器.wikitext"),
    ("Widget:SynSpirit", "src/widgets/Widget_SynSpirit.html"),
    ("Widget:复刻计时器排序", "snapshots/upstream/Widget_复刻计时器排序.html"),
]

BASE_URL = "https://wiki.biligame.com/sky/api.php"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_page(title):
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": title,
        "rvprop": "ids|flags|timestamp|user|size|comment|content",
        "format": "json"
    }
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        pages = data.get("query", {}).get("pages", {})
        for _, page in pages.items():
            rev = page.get("revisions", [{}])[0]
            return {
                "pageid": page.get("pageid"),
                "title": page.get("title"),
                "revid": rev.get("revid"),
                "timestamp": rev.get("timestamp"),
                "user": rev.get("user"),
                "comment": rev.get("comment"),
                "content": rev.get("*", "")
            }
    return None

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    meta_path = os.path.join(root, "snapshots", "rev_metadata.json")
    
    metadata = {
        "backup_time": datetime.utcnow().isoformat() + "Z",
        "pages": {}
    }

    print("=== 开始拉取 BWiki 页面与 Widget 源码 ===")
    for title, rel_path in PAGES:
        print(f"正在拉取: {title} ...")
        res = fetch_page(title)
        if not res:
            print(f"❌ 拉取失败: {title}")
            continue

        target_file = os.path.join(root, rel_path)
        os.makedirs(os.path.dirname(target_file), exist_ok=True)
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(res["content"])

        metadata["pages"][title] = {
            "pageid": res["pageid"],
            "revid": res["revid"],
            "timestamp": res["timestamp"],
            "user": res["user"]
        }
        print(f"✅ 保存成功: {rel_path} (revid: {res['revid']}, 作者: {res['user']})")

    os.makedirs(os.path.dirname(meta_path), exist_ok=True)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"✅ 元数据更新完成: {meta_path}")

if __name__ == "__main__":
    main()
