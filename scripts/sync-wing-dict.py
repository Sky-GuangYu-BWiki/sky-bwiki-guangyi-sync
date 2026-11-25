#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
光之翼中文字典提取与自动同步注入脚本
上游仓库: VincentZyuApps/koishi-plugin-wydashen-guangyi-query
从 const.ts (WingTagMap) 与 0.16.0.xml 提取全量光翼的地图分类、二级标签及先祖中文译名，
生成极简紧凑的 JSON 字典并自动注入到 Widget_SynSpirit.html 与 preview_sandbox.html。
"""

import os
import re
import json
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL_UPSTREAM_DIR = Path("G:/GGames/Minecraft/shuyeyun/qq-bot/koishi-dev/koishi-dev-8/external/wydashen-guangyi-query")
OUTPUT_DICT_PATH = REPO_ROOT / "src" / "data" / "wing-dict.json"
OUTPUT_MIN_PATH = REPO_ROOT / "src" / "data" / "wing-dict.min.json"

WIDGET_PATH = REPO_ROOT / "src" / "widgets" / "Widget_SynSpirit.html"
SANDBOX_PATH = REPO_ROOT / "test" / "preview_sandbox.html"

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

def build_compact_dict():
    print("🚀 开始同步光之翼与先祖中文字典...")
    xml_path = LOCAL_UPSTREAM_DIR / "assets" / "xml" / "0.16.0.xml"
    const_path = LOCAL_UPSTREAM_DIR / "src" / "const.ts"
    
    if not xml_path.exists() or not const_path.exists():
        raise FileNotFoundError(f"未找到本地上游文件，请检查: {LOCAL_UPSTREAM_DIR}")

    print(f"📖 读取本地化 XML: {xml_path}")
    spirit_names = extract_spirit_names_from_xml(xml_path.read_text(encoding="utf-8"))
    print(f"✅ 成功提取 {len(spirit_names)} 个先祖中文本地化名称")

    print(f"📖 读取标签映射表: {const_path}")
    wing_tag_map = extract_wing_tag_map_from_ts(const_path.read_text(encoding="utf-8"))
    print(f"✅ 成功提取 {len(wing_tag_map)} 个光之翼点位标签")

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
    print(f"🎉 紧凑字典已保存: {OUTPUT_MIN_PATH} ({len(min_str.encode('utf-8')) / 1024:.2f} KB)")
    return min_str

if __name__ == "__main__":
    build_compact_dict()
