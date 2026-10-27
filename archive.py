# -*- coding: utf-8 -*-
"""留档脚本：把保留清单里标记的条目复制到留档文件夹。只复制，永不删除/移动原件。"""
import json
import os
import shutil
import sys
from datetime import datetime
from urllib.parse import urlparse

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE, "config.json"), "r", encoding="utf-8") as f:
    CONFIG = json.load(f)


def archive_day(date_str, items):
    dest = os.path.join(CONFIG["archive_dir"], date_str)
    os.makedirs(dest, exist_ok=True)
    ok, skip = 0, 0
    links_md = os.path.join(dest, "网页链接.md")
    links = []

    for item in items:
        if item.get("type") == "file":
            src = item.get("path", "")
            if not src or not os.path.isfile(src):
                print(f"[跳过] 文件不存在: {src}")
                skip += 1
                continue
            target = os.path.join(dest, os.path.basename(src))
            base, ext = os.path.splitext(target)
            i = 1
            while os.path.exists(target):
                target = f"{base}_{i}{ext}"
                i += 1
            shutil.copy2(src, target)
            print(f"[留档] {src} -> {target}")
            ok += 1
        elif item.get("type") == "url":
            title = item.get("title") or item.get("url", "未命名")
            links.append(f"- [{title}]({item.get('url', '')})")
            ok += 1
        else:
            skip += 1

    if links:
        with open(links_md, "a", encoding="utf-8") as f:
            f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')} 留档\n")
            f.write("\n".join(links) + "\n")
    print(f"\n[汇总] 留档成功 {ok} 项，跳过 {skip} 项 -> {dest}")
    return ok, skip


def main():
    keep_dir = os.path.join(BASE, "keep")
    keep_files = [f for f in os.listdir(keep_dir) if f.endswith(".json")] if os.path.isdir(keep_dir) else []
    if not keep_files:
        print("keep 文件夹里没有保留清单（keep-日期.json）。先把报告中导出的清单放进去再运行。")
        return
    for fname in keep_files:
        path = os.path.join(keep_dir, fname)
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        date_str = payload.get("date") or fname.replace("keep-", "").replace(".json", "")
        items = payload.get("items", [])
        print(f"\n=== 处理保留清单: {fname}（{len(items)} 项）===")
        archive_day(date_str, items)
        # 处理完的清单改名归档，避免重复处理
        os.replace(path, path + ".done")
        print(f"[完成] 清单已标记处理: {fname}.done")


if __name__ == "__main__":
    main()
