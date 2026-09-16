#!/usr/bin/env python3
"""交易日判断（纯标准库，免依赖）
逻辑: 交易日 = 周一至周五 且 非法定节假日（holiday-cn 表，缓存 30 天）
输出: 首词 YES / NO / UNKNOWN（UNKNOWN = 日历源不可用，按交易日处理并提示）
用法: python3 trade_day.py [--date YYYYMMDD]
退出码: 0=YES  1=NO  2=UNKNOWN
"""
import datetime as dt
import json
import os
import sys
import time
import urllib.request

CACHE_DIR = os.path.expanduser("~/.cache/duanxianxia")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
SOURCES = [
    "https://cdn.jsdelivr.net/gh/NateScarlet/holiday-cn@master/{y}.json",
    "https://raw.githubusercontent.com/NateScarlet/holiday-cn/master/{y}.json",
]
WEEK = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def load_holidays(year):
    path = os.path.join(CACHE_DIR, f"holiday_cn_{year}.json")
    fresh = os.path.exists(path) and (time.time() - os.path.getmtime(path) < 30 * 86400)
    if not fresh:
        for url in SOURCES:
            try:
                req = urllib.request.Request(url.format(y=year), headers=UA)
                data = json.loads(urllib.request.urlopen(req, timeout=10).read().decode("utf-8"))
                os.makedirs(CACHE_DIR, exist_ok=True)
                json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False)
                return data
            except Exception:
                continue
    if os.path.exists(path):
        try:
            return json.load(open(path, encoding="utf-8"))
        except Exception:
            pass
    return None


def main():
    args = sys.argv[1:]
    if "--date" in args:
        d = dt.datetime.strptime(args[args.index("--date") + 1], "%Y%m%d").date()
    else:
        d = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).date()
    if d.weekday() >= 5:
        print(f"NO 非交易日: 周末({WEEK[d.weekday()]}) {d.isoformat()}")
        return 1
    hol = load_holidays(d.year)
    if hol is None:
        print(f"UNKNOWN 交易日历不可用（已按交易日处理） {d.isoformat()}")
        return 2
    for item in hol.get("days", []):
        if item.get("date") == d.isoformat() and item.get("isOffDay"):
            print(f"NO 非交易日: 法定节假日「{item.get('name', '')}」 {d.isoformat()}")
            return 1
    print(f"YES 交易日 {d.isoformat()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
