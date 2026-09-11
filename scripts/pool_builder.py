#!/usr/bin/env python3
"""短线侠 · 3天3板股票池与主线持续提醒

规则:
  1) 过去 N 个交易日(默认5)内出现「X天X板」(X>=3, 连续板)的股票 → 股票池
  2) 池内股票的概念标签(涨停原因) → 主线关注列表
  3) 每个交易日收盘后检查: 池内个股 / 主线概念 是否持续有涨停、连板 → 输出提醒

用法:
  python3 pool_builder.py build [--days 5]   # 重建股票池(写入状态文件)
  python3 pool_builder.py show               # 显示当前股票池与主线概念
  python3 pool_builder.py check [--date YYYYMMDD]  # 检查主线持续(默认今天), 输出提醒文本

状态文件: ~/.cache/duanxianxia/pool.json
依赖: requests
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
from collections import Counter, defaultdict

import requests

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.0 Safari/605.1.15")
BASE = "https://duanxianxia.com"
STATE_DIR = os.path.expanduser("~/.cache/duanxianxia")
STATE = os.path.join(STATE_DIR, "pool.json")


def _post(path, data):
    r = requests.post(BASE + path, data=data, headers={"User-Agent": UA}, timeout=20)
    return r.json()


def fupan_htmlcopy(date):
    return _post("/api/getFupanByYidong", {"date": date, "type": "plate"}).get("htmlcopy", "") or ""


def nav_date(date, direction="prev"):
    d = _post("/api/getFupanDate", {"date": date, "type": direction}).get("date", "")
    return d.replace("-", "")


def last_trade_dates(days=5):
    """最近 N 个交易日(含今天或最近交易日)"""
    today = dt.date.today().strftime("%Y%m%d")
    first = nav_date(today, "choose") or today
    ds = [first]
    while len(ds) < days:
        p = nav_date(ds[-1], "prev")
        if not p or p == ds[-1]:
            break
        ds.append(p)
    return ds


def _cells(hc):
    t = re.sub(r"<[^>]+>", "|", hc)
    t = re.sub(r"\s+", "", t)
    t = re.sub(r"\|+", "|", t)
    return t.split("|")


def parse_rows(hc):
    """解析复盘 HTML 中的涨停股票行 -> [{code,name,label,streak,concepts}]"""
    cs = _cells(hc)
    out = []
    i, n = 0, len(cs)
    while i < n:
        head = cs[i] or ""
        if re.match(r"^(\d+连板|首板)$", head):
            for j in range(i + 1, min(i + 7, n)):
                code, name, label = cs[j] or "", cs[j + 1] if j + 1 < n else "", cs[j + 2] if j + 2 < n else ""
                if re.match(r"^\d{6}$", code) and re.match(r"^(\d+天\d+板|首板)$", label):
                    streak = int(head[:-2]) if "连板" in head else 1
                    out.append({
                        "code": code, "name": name, "label": label,
                        "streak": streak,
                        "concepts": cs[j + 5] if j + 5 < n else "",
                    })
                    i = j + 3
                    break
            else:
                i += 1
        else:
            i += 1
    return out


def _split_concepts(s):
    return [c.strip() for c in re.split(r"[+、，,]", s or "") if c.strip()]


def build(days=5):
    ds = last_trade_dates(days)
    pool = {}
    for d in ds:
        for r in parse_rows(fupan_htmlcopy(d)):
            m = re.match(r"^(\d+)天\1板$", r["label"] or "")
            if not m or int(m.group(1)) < 3:
                continue
            p = pool.setdefault(r["code"], {
                "code": r["code"], "name": r["name"], "max_streak": 0,
                "dates": {}, "concepts": set(),
            })
            p["max_streak"] = max(p["max_streak"], r["streak"])
            p["dates"][d] = r["streak"]
            p["concepts"].update(_split_concepts(r["concepts"]))

    concept_cnt = Counter(c for p in pool.values() for c in p["concepts"])
    stocks = []
    for p in sorted(pool.values(), key=lambda x: (-x["max_streak"], x["code"])):
        stocks.append({
            "code": p["code"], "name": p["name"], "max_streak": p["max_streak"],
            "dates": p["dates"], "concepts": sorted(p["concepts"]),
        })
    state = {
        "updated": ds[0], "window": ds, "stocks": stocks,
        "concepts": dict(concept_cnt.most_common()),
    }
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    return state


def load_state():
    if not os.path.exists(STATE):
        return None
    with open(STATE) as f:
        return json.load(f)


def cmd_show():
    st = load_state() or build()
    print(f"股票池(近{len(st['window'])}个交易日 {st['window'][-1]}~{st['window'][0]} 的3天3板及以上)")
    print(f"共 {len(st['stocks'])} 只:")
    for s in st["stocks"]:
        print(f"  {s['code']} {s['name']:<6s} 最高{s['max_streak']}板  概念: {'/'.join(s['concepts'])}")
    top = [f"{c}×{n}" for c, n in list(st["concepts"].items())[:12]]
    print("高频概念: " + "、".join(top))


def cmd_check(date=None):
    st = load_state()
    if not st:
        st = build()
    date = date or dt.date.today().strftime("%Y%m%d")
    rows = parse_rows(fupan_htmlcopy(date))
    if not rows:
        print(f"✅ {date} 无复盘数据(非交易日或未更新)")
        return
    pool_codes = {s["code"]: s for s in st["stocks"]}

    # A. 池内个股持续
    cont = [r for r in rows if r["code"] in pool_codes]
    # B. 主线概念持续(池内概念 vs 今日涨停股概念)
    hits = defaultdict(list)
    for r in rows:
        rc = r["concepts"] or ""
        for c in st["concepts"]:
            if len(c) >= 2 and c in rc:
                hits[c].append(r)

    lines = [f"⚠️ 主线持续提醒 · {date}"]
    if cont:
        lines.append("【池内个股续板】" + "、".join(f"{r['name']}({r['label']})" for r in cont))
    strong = []
    for c, rs in sorted(hits.items(), key=lambda kv: -len(kv[1])):
        lb = [x for x in rs if x["streak"] >= 2]
        if len(rs) >= 2 or lb:
            tag = f"{c}×{len(rs)}"
            if lb:
                tag += "(连板:" + "、".join(f"{x['name']}{x['label']}" for x in lb) + ")"
            strong.append(tag)
    if strong:
        lines.append("【主线概念持续】" + "；".join(strong[:8]))
    if len(lines) == 1:
        lines.append("✅ 池内个股与主线概念今日无涨停/连板延续")
    else:
        lines.append(f"（股票池共{len(st['stocks'])}只，主跟踪{len(st['concepts'])}个概念；仅为节奏参考，不构成投资建议）")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(description="3天3板股票池与主线持续提醒")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--days", type=int, default=5)
    c = sub.add_parser("check")
    c.add_argument("--date", default=None)
    sub.add_parser("show")
    a = ap.parse_args()
    if a.cmd == "build":
        st = build(a.days)
        print(f"已重建股票池: {len(st['stocks'])}只 / {len(st['concepts'])}个概念 (窗口 {st['window'][-1]}~{st['window'][0]})")
    elif a.cmd == "show":
        cmd_show()
    elif a.cmd == "check":
        cmd_check(a.date)


if __name__ == "__main__":
    main()
