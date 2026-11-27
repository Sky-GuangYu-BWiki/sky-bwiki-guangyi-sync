#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
光之翼中文字典提取与自动同步脚本 (sync_wing_dict.py)
================================================================================
上游仓库: VincentZyuApps/koishi-plugin-wydashen-guangyi-query
依赖工具: GitHub CLI (gh)

功能说明:
  通过 gh cli 自动从上游远程仓库拉取最新的：
    1. src/const.ts (WingTagMap 光翼点位与标签映射表)
    2. assets/xml/0.16.0.xml (先祖中英文本地化对照表)
  解析生成全量紧凑的 JSON 中文字典，并输出到:
    - src/data/wing-dict.json (完整格式化版)
    - src/data/wing-dict.min.json (极简内嵌版，供 Widget 使用)

代理用法示例 (国内网络推荐配置本机代理):
--------------------------------------------------------------------------------
1. 命令行参数方式 (推荐):
   python scripts/sync_wing_dict.py --proxy http://127.0.0.1:7890

2. 环境变量方式:
   # PowerShell:
   $env:HTTP_PROXY="http://127.0.0.1:7890"; $env:HTTPS_PROXY="http://127.0.0.1:7890"
   python scripts/sync_wing_dict.py

   # Bash:
   HTTP_PROXY=http://127.0.0.1:7890 HTTPS_PROXY=http://127.0.0.1:7890 python3 scripts/sync_wing_dict.py

3. 指定自定义上游分支或仓库:
   python scripts/sync_wing_dict.py --repo VincentZyuApps/koishi-plugin-wydashen-guangyi-query --branch main --proxy http://127.0.0.1:7890
================================================================================
"""

import os
import sys
import re
import json
import argparse
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DICT_PATH = REPO_ROOT / "src" / "data" / "wing-dict.json"
OUTPUT_MIN_PATH = REPO_ROOT / "src" / "data" / "wing-dict.min.json"

DEFAULT_UPSTREAM_REPO = "VincentZyuApps/koishi-plugin-wydashen-guangyi-query"
DEFAULT_BRANCH = "main"

def parse_args():
    parser = argparse.ArgumentParser(description="从上游 GitHub 仓库通过 gh cli 提取光之翼中文字典")
    parser.add_argument("--repo", default=DEFAULT_UPSTREAM_REPO, help="上游 GitHub 仓库 (默认: VincentZyuApps/koishi-plugin-wydashen-guangyi-query)")
    parser.add_argument("--branch", default=DEFAULT_BRANCH, help="上游分支名 (默认: main)")
    parser.add_argument("--proxy", default=None, help="HTTP/HTTPS 代理地址 (例如: http://127.0.0.1:7890)")
    parser.add_argument("--local-dir", default=None, help="可选本地 fallback 源码目录 (如提供则优先从本地读取)")
    return parser.parse_args()

def fetch_file_via_gh(repo: str, file_path: str, branch: str, proxy: str = None) -> str:
    """调用 gh cli 获取指定仓库文件的 raw 文本内容"""
    endpoint = f"/repos/{repo}/contents/{file_path}?ref={branch}"
    cmd = [
        "gh", "api", endpoint,
        "-H", "Accept: application/vnd.github.raw+json"
    ]
    
    env = os.environ.copy()
    if proxy:
        env["HTTP_PROXY"] = proxy
        env["HTTPS_PROXY"] = proxy
        env["http_proxy"] = proxy
        env["https_proxy"] = proxy

    print(f"📡 通过 gh cli 拉取远程文件: {repo}/{file_path} (ref={branch}) ...")
    try:
        proc = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True
        )
        return proc.stdout
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.strip() if e.stderr else str(e)
        raise RuntimeError(f"调用 gh api 失败 [{file_path}]: {err_msg}")
    except FileNotFoundError:
        raise RuntimeError("未检测到 gh 命令，请确认已安装 GitHub CLI 并已登录 (gh auth login)")

def extract_spirit_names_from_xml(xml_content: str) -> dict:
    spirit_map = {}
    root = ET.fromstring(xml_content)
    for string_node in root.findall(".//string"):
        name_attr = string_node.attrib.get("name", "")
        if name_attr.startswith("name_"):
            eng_name = name_attr[5:]
            base_eng_name = re.sub(r'_\d+$', '', eng_name)
            chinese_name = (string_node.text or "").strip()
            if base_eng_name and chinese_name:
                spirit_map[base_eng_name] = chinese_name
    return spirit_map

def extract_wing_tag_map_from_ts(ts_content: str) -> list:
    m = re.search(r'export\s+const\s+WingTagMap\s*=\s*(\[.*?\])\s*as\s+const', ts_content, re.DOTALL)
    if not m:
        m = re.search(r'export\s+const\s+WingTagMap\s*=\s*(\[.*?\]);?', ts_content, re.DOTALL)
    if not m:
        raise ValueError("无法在 const.ts 中匹配到 WingTagMap 数组")
    
    clean_json = re.sub(r'//.*', '', m.group(1))
    clean_json = re.sub(r',\s*\]', ']', clean_json)
    return json.loads(clean_json)

def extract_base_spirit_name(wing_name: str) -> str:
    if not wing_name.startswith("s_"):
        return ""
    base = wing_name[2:]
    return re.sub(r'_\d+$', '', base)

def main():
    args = parse_args()
    print("=== [sync_wing_dict] 开始同步光之翼与先祖中文字典 ===")
    if args.proxy:
        print(f"🌐 已配置代理参数: {args.proxy}")
    elif os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY"):
        print(f"🌐 检测到环境变量代理: {os.environ.get('HTTP_PROXY') or os.environ.get('HTTPS_PROXY')}")

    xml_content = None
    const_content = None

    # 1. 检查是否有本地 fallback 目录
    if args.local_dir and Path(args.local_dir).is_dir():
        local_dir = Path(args.local_dir)
        local_xml = local_dir / "assets" / "xml" / "0.16.0.xml"
        local_const = local_dir / "src" / "const.ts"
        if local_xml.exists() and local_const.exists():
            print(f"📂 从本地 fallback 目录读取: {local_dir}")
            xml_content = local_xml.read_text(encoding="utf-8")
            const_content = local_const.read_text(encoding="utf-8")

    # 2. 默认通过 gh cli 远程拉取
    if not xml_content or not const_content:
        xml_content = fetch_file_via_gh(args.repo, "assets/xml/0.16.0.xml", args.branch, args.proxy)
        const_content = fetch_file_via_gh(args.repo, "src/const.ts", args.branch, args.proxy)

    print("📖 解析本地化 XML 先祖字典...")
    spirit_names = extract_spirit_names_from_xml(xml_content)
    print(f"✅ 成功解析 {len(spirit_names)} 个先祖中文本地化译名")

    print("📖 解析 TypeScript 点位标签映射表...")
    wing_tag_map = extract_wing_tag_map_from_ts(const_content)
    print(f"✅ 成功解析 {len(wing_tag_map)} 个光之翼点位标签")

    compact_dict = {}
    for item in wing_tag_map:
        wing_id = item.get("光翼名字", "").strip()
        cat = item.get("一级标签", "").strip()
        sub = item.get("二级标签", "").strip()
        
        display_name = ""
        if wing_id.startswith("s_"):
            base_name = extract_base_spirit_name(wing_id)
            display_name = spirit_names.get(base_name, base_name)
        else:
            display_name = f"{cat}地图光翼" if not sub else f"{cat}-{sub}"

        compact_dict[wing_id] = [cat, sub, display_name]

    OUTPUT_DICT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_DICT_PATH.write_text(json.dumps(compact_dict, ensure_ascii=False, indent=2), encoding="utf-8")
    
    min_str = json.dumps(compact_dict, ensure_ascii=False, separators=(',', ':'))
    OUTPUT_MIN_PATH.write_text(min_str, encoding="utf-8")
    
    file_size_kb = len(min_str.encode('utf-8')) / 1024
    print(f"🎉 紧凑字典已成功生成: {OUTPUT_MIN_PATH} ({file_size_kb:.2f} KB)")
    print("=== 同步完成 ===")

if __name__ == "__main__":
    main()
