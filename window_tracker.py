# -*- coding: utf-8 -*-
"""前台窗口实时监控：每 10 秒采样当前活动窗口，记录活动片段（程序名+标题+起止时间）。
空闲超过 5 分钟自动暂停记录。输出 data/window-YYYY-MM-DD.json"""
import ctypes
import ctypes.wintypes as wt
import json
import os
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "data")
POLL_SECONDS = 10
IDLE_PAUSE_SECONDS = 300  # 空闲 5 分钟视为离开，不计入活动

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

PROCESS_NAME_CACHE = {}


def get_active_window():
    """返回 (程序名, 窗口标题) 或 None"""
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    title = buf.value.strip()
    # 取该窗口所属进程名
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    exe = PROCESS_NAME_CACHE.get(pid.value)
    if not exe:
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if h:
            name_buf = ctypes.create_unicode_buffer(260)
            size = wt.DWORD(260)
            if kernel32.QueryFullProcessImageNameW(h, 0, name_buf, ctypes.byref(size)):
                exe = os.path.basename(name_buf.value)
            kernel32.CloseHandle(h)
        PROCESS_NAME_CACHE[pid.value] = exe or "unknown"
    return exe or "unknown", title


def get_idle_seconds():
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", wt.UINT), ("dwTime", wt.DWORD)]
    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(LASTINPUTINFO)
    user32.GetLastInputInfo(ctypes.byref(info))
    now_tick = kernel32.GetTickCount()
    return (now_tick - info.dwTime) / 1000.0


def day_path():
    return os.path.join(DATA_DIR, f"window-{datetime.now().strftime('%Y-%m-%d')}.json")


def load_data():
    p = day_path()
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"date": datetime.now().strftime("%Y-%m-%d"), "segments": []}


def save_data(data):
    tmp = day_path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, day_path())


def close_segment(data, seg):
    """片段落盘：不足 30 秒的碎片丢弃"""
    end = datetime.now()
    dur = (end - seg["end"]).total_seconds()
    if dur < 30:
        return
    data["segments"].append({
        "app": seg["app"], "title": seg["title"],
        "start": seg["start"].strftime("%H:%M:%S"),
        "end": end.strftime("%H:%M:%S"),
        "minutes": round(dur / 60, 1),
    })
    save_data(data)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"[启动] 窗口监控运行中，每 {POLL_SECONDS}s 采样，数据写入 data/")
    data = load_data()
    current = None  # {"app","title","start","end"}
    while True:
        try:
            if get_idle_seconds() > IDLE_PAUSE_SECONDS:
                if current:
                    close_segment(data, current)
                    current = None
                ctypes.windll.user32.SetCursorPos(0, 0) if False else None
                import time
                time.sleep(POLL_SECONDS * 6)  # 空闲时降频
                continue
            win = get_active_window()
            if win:
                app, title = win
                if title:
                    now = datetime.now()
                    if current and current["app"] == app and current["title"] == title:
                        current["end"] = now  # 同一活动延续
                    else:
                        if current:
                            close_segment(data, current)
                        current = {"app": app, "title": title, "start": now, "end": now}
        except Exception as e:
            print(f"[警告] {e}")
        import time
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
