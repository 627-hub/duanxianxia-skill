#!/usr/bin/env python3
"""交易日判断（纯标准库，免依赖）
校验顺序（fail-open）：
  1) 深交所官方日历（权威，含节假日与调休；按月缓存 30 天）→ 不可用时降级
  2) holiday-cn 推算（周一至周五 且 非法定节假日）
  3) 均不可用 → UNKNOWN（按交易日处理并提示）
输出: 首词 YES / NO / UNKNOWN（后附来源）
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


def szse_open(d):
    """深交所官方日历：True=开市 / False=休市 / None=不可用（按月缓存）"""
    cache = os.path.join(CACHE_DIR, f"szse_cal_{d.year}-{d.month:02d}.json")
    key = d.isoformat()

    def read_cache():
        try:
            obj = json.load(open(cache, encoding="utf-8"))
            days = obj.get("days") or {}
            return obj, days
        except Exception:
            return None, None

    obj, days = read_cache()
    fresh = bool(obj) and (time.time() - obj.get("_fetched", 0) < 30 * 86400)
    if not (days and key in days and fresh):
        try:
            h = dict(UA)
            h["Referer"] = "https://www.szse.cn/"
            url = ("https://www.szse.cn/api/report/exchange/onepersistenthour/monthList"
                   f"?month={d.year}-{d.month}")
            req = urllib.request.Request(url, headers=h)
            j = json.loads(urllib.request.urlopen(req, timeout=10).read().decode("utf-8"))
            new_days = {str(r.get("jyrq", ""))[:10]: str(r.get("jybz")) for r in (j.get("data") or [])}
            if new_days:
                days = new_days
                os.makedirs(CACHE_DIR, exist_ok=True)
                json.dump({"_fetched": time.time(), "days": days},
                          open(cache, "w", encoding="utf-8"))
        except Exception:
            pass  # 保留旧缓存（若含当日）
    if days and key in days:
        return days[key] == "1"
    return None


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

    # 1) 深交所官方日历（权威）
    flag = szse_open(d)
    if flag is True:
        print(f"YES 交易日 {d.isoformat()}（深交所官方日历）")
        return 0
    if flag is False:
        print(f"NO 非交易日: 深交所官方日历（休市/节假日） {d.isoformat()}")
        return 1

    # 2) 降级 holiday-cn 推算
    if d.weekday() >= 5:
        print(f"NO 非交易日: 周末({WEEK[d.weekday()]}) {d.isoformat()}（holiday-cn 推算）")
        return 1
    hol = load_holidays(d.year)
    if hol is None:
        print(f"UNKNOWN 交易日历不可用（已按交易日处理） {d.isoformat()}")
        return 2
    for item in hol.get("days", []):
        if item.get("date") == d.isoformat() and item.get("isOffDay"):
            print(f"NO 非交易日: 法定节假日「{item.get('name', '')}」 {d.isoformat()}（holiday-cn 推算）")
            return 1
    print(f"YES 交易日 {d.isoformat()}（holiday-cn 推算，官方日历不可用）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
