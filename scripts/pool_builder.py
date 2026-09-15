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


import time as _time
import random as _random

_LAST_REQ = [0.0]
_MIN_INTERVAL = 10.0  # 短线侠限流: 免费接口≥10秒/次, 避免触发IP风控(实测密集调用会整站403)

def _throttle():
    wait = _MIN_INTERVAL - (_time.time() - _LAST_REQ[0])
    if wait > 0:
        _time.sleep(wait + _random.uniform(0.2, 0.8))
    _LAST_REQ[0] = _time.time()


def _post(path, data):
    _throttle()
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
            # 口径: 「X天Y板」且 Y>=3 (含非连续组合如4天3板/5天3板), 或纯连板 streak>=3
            m = re.match(r"^(\d+)天(\d+)板$", r["label"] or "")
            days_n = int(m.group(1)) if m else None
            boards_n = int(m.group(2)) if m else None
            if boards_n is not None:
                if boards_n < 3:
                    continue
            elif r["streak"] < 3:
                continue
            p = pool.setdefault(r["code"], {
                "code": r["code"], "name": r["name"], "max_streak": 0,
                "dates": {}, "concepts": set(),
            })
            # max_streak 取板数口径(boards_n 优先, 否则 streak), 用于排序
            eff = boards_n if boards_n is not None else r["streak"]
            p["max_streak"] = max(p["max_streak"], eff)
            p["dates"][d] = eff
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


def _tx_quotes(codes):
    """腾讯批量行情 → {code: {name, pct, close}}"""
    prefix = lambda c: ("sh" if c.startswith("6") else ("bj" if c.startswith(("4", "8", "92")) else "sz")) + c
    out = {}
    for i in range(0, len(codes), 60):
        batch = codes[i:i+60]
        url = "https://qt.gtimg.cn/q=" + ",".join(prefix(c) for c in batch)
        r = requests.get(url, headers={"User-Agent": UA, "Referer": "https://gu.qq.com/"}, timeout=10)
        r.encoding = "gbk"
        for line in r.text.strip().split(";"):
            if "~" not in line:
                continue
            f = line.split("~")
            if len(f) < 34:
                continue
            try:
                out[f[2]] = {"name": f[1], "pct": float(f[32]), "close": float(f[3])}
            except (ValueError, IndexError):
                pass
    return out


def _tx_daily(code, n=6):
    """腾讯日K → [(date, open, close, high, low, vol)] 正序"""
    mkt = "sh" if code.startswith("6") else ("bj" if code.startswith(("4", "8", "92")) else "sz")
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={mkt}{code},day,,,{n},qfq"
    try:
        d = requests.get(url, headers={"User-Agent": UA}, timeout=10).json()["data"][mkt + code]
        k = d.get("qfqday") or d.get("day") or []
        return [(x[0], float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[5])) for x in k]
    except Exception:
        return []


def cmd_roles(date=None):
    """收盘后对池内票标注组内角色: 连板/断板/分歧 + 昨日量能(放量/缩量一字)。
    写入 pool.json 的 roles 字段, 供次日盘前竞价任务直接读取比选。"""
    st = load_state() or build()
    date = date or dt.date.today().strftime("%Y%m%d")
    pool = {s["code"]: s for s in st["stocks"]}
    if not pool:
        print("股票池为空, 先 build")
        return

    # 1) 今日涨停票及板数标签
    rows_today = parse_rows(fupan_htmlcopy(date))
    zt_today = {r["code"]: r for r in rows_today}
    # 2) 昨日涨停票(池内)
    prev_d = None
    try:
        prev_d = nav_date(date, "prev")
    except Exception:
        pass
    rows_prev = parse_rows(fupan_htmlcopy(prev_d)) if prev_d else []
    zt_prev = {r["code"]: r for r in rows_prev}

    # 3) 今日行情(判定断板: 昨日涨停今日未涨停)
    quotes = _tx_quotes(list(pool.keys()))

    roles = {}
    for code, s in pool.items():
        q = quotes.get(code)
        in_zt_today = code in zt_today
        in_zt_prev = code in zt_prev
        # 组内角色
        if in_zt_today:
            r_today = zt_today[code]
            m = re.match(r"^(\d+)天(\d+)板$", r_today["label"] or "")
            boards = int(m.group(2)) if m else r_today["streak"]
            role = "连板" if (boards >= 2 or in_zt_prev) else "首板"
            detail = r_today["label"]
        elif in_zt_prev and q is not None and q["pct"] < 9.8:
            role = "断板"
            detail = f"昨涨停今日{q['pct']:+.1f}%"
        else:
            # 分歧判定: 近5日宽幅震荡(任一日振幅>12% 且非一字)
            k = _tx_daily(code, 6)
            wide = sum(1 for x in k if (x[3] - x[4]) / max(x[2], 0.01) > 0.12)
            role = "分歧" if wide >= 2 else "观察"
            detail = f"近5日宽幅{wide}天" if k else "K线缺失"
        # 昨日量能(用于唯一连板回流/分歧预案): 昨日一字缩量 vs 放量
        vol_tag = ""
        k = _tx_daily(code, 6)
        if in_zt_prev and len(k) >= 2:
            y = k[-2]  # 昨日(数据截至今日, 倒数第2根=昨日)
            o, c, h, l, v = y[1], y[2], y[3], y[4], y[5]
            is_yzt = (c > o * 1.095) or (c >= h * 0.998 and c > o * 1.09)
            if is_yzt:
                one_word = abs(h - l) / max(c, 0.01) < 0.015  # 全天振幅<1.5% = 一字
                # 放量: 昨日量 > 前日量*1.5
                vol_up = len(k) >= 3 and v > k[-3][5] * 1.5
                vol_tag = "一字缩量" if one_word else ("放量" if vol_up else "常量")
        roles[code] = {"name": s["name"], "role": role, "detail": detail,
                       "concepts": s["concepts"][:3], "prev_vol": vol_tag,
                       "max_streak": s["max_streak"]}

    # 唯一连板+放量 标记(概念温度计)
    concept_lb = defaultdict(list)
    for code, r in roles.items():
        if r["role"] == "连板":
            for c in r["concepts"]:
                concept_lb[c].append(code)
    for code, r in roles.items():
        r["unique_lianban"] = False
        if r["role"] == "连板" and r["prev_vol"] == "放量":
            for c in r["concepts"]:
                if len(concept_lb.get(c, [])) == 1:
                    r["unique_lianban"] = True
                    break

    # 写入状态文件
    st["roles_date"] = date
    st["roles"] = roles
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE, "w") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)

    # 输出梯队角色表(按角色排序: 连板>断板>分歧/观察)
    order = {"连板": 0, "断板": 1, "分歧": 2, "观察": 3, "首板": 4}
    print(f"梯队角色表 · {date} (已写入 pool.json)")
    for code, r in sorted(roles.items(), key=lambda kv: (order.get(kv[1]["role"], 9), -kv[1]["max_streak"])):
        flag = " ⭐唯一连板+放量" if r["unique_lianban"] else ""
        vol = f" 昨日{r['prev_vol']}" if r["prev_vol"] else ""
        print(f"  [{r['role']}] {code} {r['name']:<6s} {r['detail']}{vol} "
              f"概念:{'/'.join(r['concepts'])}{flag}")


def main():
    ap = argparse.ArgumentParser(description="3天3板股票池与主线持续提醒")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--days", type=int, default=5)
    c = sub.add_parser("check")
    c.add_argument("--date", default=None)
    r = sub.add_parser("roles")
    r.add_argument("--date", default=None)
    sub.add_parser("show")
    a = ap.parse_args()
    if a.cmd == "build":
        st = build(a.days)
        print(f"已重建股票池: {len(st['stocks'])}只 / {len(st['concepts'])}个概念 (窗口 {st['window'][-1]}~{st['window'][0]})")
    elif a.cmd == "show":
        cmd_show()
    elif a.cmd == "check":
        cmd_check(a.date)
    elif a.cmd == "roles":
        cmd_roles(a.date)


if __name__ == "__main__":
    main()
