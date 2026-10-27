# -*- coding: utf-8 -*-
"""学习活动收集器：读取浏览器历史 + 扫描当天文件变动，汇总到 data/YYYY-MM-DD.json"""
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, parse_qs, unquote

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE, "config.json")
DATA_DIR = os.path.join(BASE, "data")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)


def today_midnight():
    now = datetime.now()
    return datetime(now.year, now.month, now.day)


def chrome_time_to_dt(ts):
    """Chromium 时间戳：1601-01-01 起的微秒数（UTC）"""
    if not ts:
        return None
    try:
        utc = datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=ts)
        return utc.astimezone()
    except (OverflowError, OSError, ValueError):
        return None


def extract_search(url, title):
    """识别搜索行为，返回 (引擎, 关键词) 或 None"""
    try:
        p = urlparse(url)
        host = (p.netloc or "").lower()
        path = p.path or ""
        engines = [
            ("百度", "baidu.com", "/s"), ("必应", "bing.com", "/search"),
            ("谷歌", "google.", "/search"), ("360搜索", "so.com", "/s"),
            ("搜狗", "sogou.com", "/web"), ("夸克搜索", "quark.sm.cn", "/s"),
            ("知乎", "zhihu.com", "/search"), ("B站", "bilibili.com", "/search"),
            ("CSDN", "so.csdn.net", "/so"), ("掘金", "juejin.cn", "/search"),
        ]
        for name, host_key, path_key in engines:
            if host_key in host and path.startswith(path_key):
                qs = parse_qs(p.query)
                for param in CONFIG["search_param_names"]:
                    if param in qs and qs[param]:
                        return name, unquote(qs[param][0]).strip()
        return None
    except (ValueError, AttributeError):
        return None


def collect_browser_history(since):
    """复制历史库后读取当天浏览记录（避免浏览器锁库）"""
    visits, searches = [], []
    tmp_dir = tempfile.mkdtemp(prefix="ltracker_")
    try:
        for browser in CONFIG["browsers"]:
            src = browser["history_path"]
            name = browser["name"]
            if not os.path.exists(src):
                print(f"[跳过] {name} 历史库不存在: {src}")
                continue
            tmp_db = os.path.join(tmp_dir, f"{name}_history")
            try:
                shutil.copy2(src, tmp_db)
                conn = sqlite3.connect(tmp_db)
                rows = conn.execute(
                    "SELECT url, title, last_visit_time FROM urls "
                    "WHERE last_visit_time >= ? AND hidden = 0 ORDER BY last_visit_time",
                    (int(since.timestamp() * 1_000_000 + 11644473600_000_000),),
                ).fetchall()
                conn.close()
            except (sqlite3.Error, OSError) as e:
                print(f"[警告] 读取 {name} 失败: {e}")
                continue
            for url, title, ts in rows:
                dt = chrome_time_to_dt(ts)
                if not dt:
                    continue
                dt = dt.replace(tzinfo=None)  # 统一为本地朴素时间再比较
                if dt < since:
                    continue
                if not url.startswith(("http://", "https://")):
                    continue
                host = urlparse(url).netloc
                visits.append({
                    "time": dt.strftime("%H:%M"), "browser": name,
                    "title": (title or "").strip() or url, "host": host, "url": url,
                })
                hit = extract_search(url, title)
                if hit:
                    engine, query = hit
                    if query:
                        searches.append({
                            "time": dt.strftime("%H:%M"), "engine": engine, "query": query,
                        })
            print(f"[OK] {name}: 当天记录 {len(rows)} 条")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    return visits, searches


def should_skip_dir(dirname):
    return dirname in CONFIG["exclude_dir_names"] or dirname.startswith((".", "$"))


def should_skip_file(name):
    return any(pat in name for pat in CONFIG["exclude_file_patterns"])


def collect_file_activity(since, max_mtime):
    """扫描指定目录中当天新建/修改过的文件"""
    files, scanned = [], 0
    for root_dir in CONFIG["scan_dirs"]:
        if not os.path.isdir(root_dir):
            print(f"[跳过] 扫描目录不存在: {root_dir}")
            continue
        for cur, dirs, names in os.walk(root_dir):
            dirs[:] = [d for d in dirs if not should_skip_dir(d)]
            for fname in names:
                if should_skip_file(fname):
                    continue
                path = os.path.join(cur, fname)
                try:
                    st = os.stat(path)
                except OSError:
                    continue
                mtime = datetime.fromtimestamp(st.st_mtime)
                if mtime < since or mtime > max_mtime:
                    continue
                ctime = datetime.fromtimestamp(st.st_ctime)
                action = "新建" if ctime >= since else "修改"
                files.append({
                    "time": mtime.strftime("%H:%M"), "action": action,
                    "name": fname, "ext": os.path.splitext(fname)[1].lower(),
                    "dir": cur, "path": path, "size": st.st_size,
                })
                scanned += 1
                if scanned >= CONFIG["max_files"]:
                    print(f"[提示] 达到单日文件上限 {CONFIG['max_files']}，停止扫描")
                    return files
        print(f"[OK] 扫描完成: {root_dir}")
    return files


def load_existing(day_path):
    if os.path.exists(day_path):
        try:
            with open(day_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return None


def merge_records(existing, visits, searches, files):
    """与已有数据合并去重（增量收集不重复计数）"""
    if existing:
        visits = existing.get("visits", []) + visits
        searches = existing.get("searches", []) + searches
        files = existing.get("files", []) + files
    visits = {v["url"] + "|" + v["time"]: v for v in visits}
    searches = {s["query"] + "|" + s["time"]: s for s in searches}
    files = {f["path"] + "|" + f["time"]: f for f in files}
    dedup = lambda items, key: sorted(items, key=key)
    return (dedup(visits.values(), lambda x: x["time"]),
            dedup(searches.values(), lambda x: x["time"]),
            dedup(files.values(), lambda x: x["time"]))


def main():
    since = today_midnight()
    max_mtime = datetime.now() + timedelta(minutes=5)
    date_str = since.strftime("%Y-%m-%d")
    day_path = os.path.join(DATA_DIR, f"{date_str}.json")

    visits, searches = collect_browser_history(since)
    files = collect_file_activity(since, max_mtime)
    visits, searches, files = merge_records(load_existing(day_path), visits, searches, files)

    data = {
        "date": date_str,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "searches": searches,
        "visits": visits,
        "files": files,
    }
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(day_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"[完成] {date_str}: 搜索 {len(searches)} 条 / 浏览 {len(visits)} 页 / 文件 {len(files)} 个")
    print(f"[输出] {day_path}")


if __name__ == "__main__":
    main()
