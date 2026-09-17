#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""盘前隔夜公告扫描（8:30 模式）：昨18:00 → 今08:30 新发布公告，三级判定。

复用 cninfo_health.py 的取数/分类逻辑（column 固定 szse，orgId 官方映射表）。
用法: python3 overnight_scan.py 000993 605058 --date 20260917 [--start-hour 18 --end-hour 8.5]
输出: ~/.cache/duanxianxia/overnight_YYYY-MM-DD.json
限流: 巨潮请求间隔 ≥1.2s；每票公告列表 ≤10 条；单票 PDF ≤1 份（最新命中）。
"""
import argparse
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cninfo_health import OUT, load_orgids, pub_date, pdf_text, query, classify  # noqa

KEYS = ("异常波动", "风险提示", "关注函", "问询函", "立案", "处罚")


def ann_ts(ann):
    """公告发布时间戳（秒）；缺失则用 pub_date 按 00:00 兜底。"""
    t = ann.get("announcementTime")
    if isinstance(t, (int, float)) and t > 0:
        return float(t) / 1000.0
    d = pub_date(ann)
    if d:
        return dt.datetime.strptime(d, "%Y-%m-%d").timestamp()
    return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("codes", nargs="+")
    ap.add_argument("--date", default=dt.date.today().strftime("%Y%m%d"))
    ap.add_argument("--start-hour", type=float, default=18.0)   # 昨日 18:00
    ap.add_argument("--end-hour", type=float, default=8.5)      # 今日 08:30
    ap.add_argument("--month", type=int, default=35)
    a = ap.parse_args()

    today = dt.datetime.strptime(a.date, "%Y%m%d")
    t_lo = (today - dt.timedelta(days=1)).replace(
        hour=int(a.start_hour), minute=int(round((a.start_hour % 1) * 60)), second=0)
    t_hi = today.replace(hour=int(a.end_hour), minute=int(round((a.end_hour % 1) * 60)), second=0)
    lo, hi = t_lo.timestamp(), t_hi.timestamp()
    start = (today - dt.timedelta(days=1)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")
    mstart = (today - dt.timedelta(days=a.month)).strftime("%Y-%m-%d")

    print(f"[窗口] {t_lo:%Y-%m-%d %H:%M} → {t_hi:%Y-%m-%d %H:%M}  (seDate {start}~{end})", flush=True)
    org = load_orgids()
    print(f"[orgid表] {len(org)} 条", flush=True)

    result = []
    for code in a.codes:
        oid = org.get(code, "")
        try:
            anns = query(code, oid, start, end)
        except Exception as e:
            print(f"[{code}] 查询失败 {e}", flush=True)
            result.append({"code": code, "error": str(e)})
            continue
        # 一月内异动公告次数（用于「第3次及以上」判定）
        ycount = 0
        try:
            ym = query(code, oid, mstart, end)
            ycount = sum(1 for x in ym if "异常波动" in (x.get("announcementTitle") or ""))
        except Exception:
            pass
        new = [x for x in anns if lo <= ann_ts(x) <= hi]
        new = sorted(new, key=ann_ts, reverse=True)[:10]
        rec = {"code": code, "orgId": oid, "new_count": len(new),
               "month_yidong_count": ycount,
               "titles": [f"{dt.datetime.fromtimestamp(ann_ts(x)):%m-%d %H:%M} {x.get('announcementTitle')}"
                          for x in new],
               "hits": []}
        hits = [x for x in new if any(k in (x.get("announcementTitle") or "") for k in KEYS)]
        for x in hits[:1]:  # 单票 PDF 最多 1 份（最新命中）
            title = x.get("announcementTitle") or ""
            try:
                txt = pdf_text(x.get("adjunctUrl") or "")
            except Exception as e:
                txt = f"[PDF失败 {e}]"
            lvl, why, quote = classify(title, txt, ycount)
            if any(k in title for k in ("立案", "处罚")):
                if lvl == "🟡":
                    lvl = "🟠"
                why = f"立案/处罚类公告（{why}）"
            rec["hits"].append({"date": f"{dt.datetime.fromtimestamp(ann_ts(x)):%Y-%m-%d %H:%M}",
                                "title": title, "level": lvl, "reason": why, "quote": quote,
                                "pdf_ok": not txt.startswith("[")})
        result.append(rec)
        print(f"[{code}] 隔夜新公告{len(new)}条 / 一月异动{ycount}次 / 命中{len(hits)}", flush=True)
        for t in rec["titles"]:
            print(f"    · {t}", flush=True)
        for h in rec["hits"]:
            print(f"    {h['level']} {h['date']} {h['title']} | {h['reason']} | {h['quote'][:200]}", flush=True)

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"overnight_{a.date}.json")
    json.dump(result, open(path, "w"), ensure_ascii=False, indent=1)
    print("SAVED", path)


if __name__ == "__main__":
    main()
