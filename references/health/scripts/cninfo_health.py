#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""巨潮公告深查 v2：异常波动/风险提示三级判定
修正: column 固定 szse (2026-09-16 实测 shse 返回0条)
用法: python3 cninfo_health.py 000993 605058 --date 20260916
"""
import argparse
import json
import os
import re
import subprocess
import time
import urllib.parse
import urllib.request
import datetime as dt

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
CNINFO = "http://www.cninfo.com.cn"
PDF_DIR = "/tmp/dxx_health_pdf"
OUT = os.path.expanduser("~/.cache/duanxianxia")

_last = [0.0]
def throttle(sec=1.2):
    w = sec - (time.time() - _last[0])
    if w > 0:
        time.sleep(w)
    _last[0] = time.time()


def http(url, data=None, headers=None, timeout=30, retries=3):
    h = {"User-Agent": UA, "Referer": CNINFO + "/new/index"}
    if headers:
        h.update(headers)
    body = urllib.parse.urlencode(data).encode() if data else None
    last = None
    for i in range(retries):
        try:
            throttle()
            return urllib.request.urlopen(urllib.request.Request(url, data=body, headers=h),
                                          timeout=timeout).read().decode("utf-8", "ignore")
        except Exception as e:
            last = e
            time.sleep(1.5 * (i + 1))
    raise last


def load_orgids():
    d = json.loads(http(CNINFO + "/new/data/szse_stock.json"))
    lst = d.get("stockList") or d
    return {x["code"]: x["orgId"] for x in lst if x.get("code")}


def query(code, orgid, start, end):
    data = {"pageNum": 1, "pageSize": 40, "column": "szse", "tabName": "fulltext",
            "plate": "", "stock": f"{code},{orgid}" if orgid else code, "searchkey": "",
            "secid": "", "category": "", "trade": "", "seDate": f"{start}~{end}",
            "sortName": "", "sortType": "", "isHLtitle": "true"}
    j = json.loads(http(CNINFO + "/new/hisAnnouncement/query", data,
                        headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                                 "X-Requested-With": "XMLHttpRequest"}))
    return j.get("announcements") or []


def pub_date(ann):
    m = re.search(r"/(\d{4}-\d{2}-\d{2})/", ann.get("adjunctUrl") or "")
    return m.group(1) if m else ""


def pdf_text(adjunct_url):
    os.makedirs(PDF_DIR, exist_ok=True)
    fn = os.path.join(PDF_DIR, os.path.basename(adjunct_url))
    if not os.path.exists(fn):
        raw = urllib.request.urlopen(urllib.request.Request(
            "http://static.cninfo.com.cn/" + adjunct_url, headers={"User-Agent": UA}), timeout=60).read()
        open(fn, "wb").write(raw)
    with open(fn, "rb") as f:
        head = f.read(5)
    if not head.startswith(b"%PDF"):
        return "[PDF内容非PDF]"
    try:
        out = subprocess.run(["pdftotext", "-layout", fn, "-"], capture_output=True, timeout=90)
        return out.stdout.decode("utf-8", "ignore")
    except Exception as e:
        return f"[pdftotext失败 {e}]"


STRONG = [("击鼓传花", "「击鼓传花」字样"),
          ("炒作情绪过热", "「炒作情绪过热」"),
          ("非理性炒作", "「非理性炒作」"),
          ("勿受市场情绪过热", "「勿受市场情绪过热影响」"),
          ("受市场情绪过热影响", "「受市场情绪过热影响」")]


def extract_quote(text, title):
    """优先抓强负面前提句（非理性炒作/击鼓传花），其次过热/换手率句，最后「特别提示」段"""
    t = re.sub(r"[ \t\u3000]+", "", text or "")
    for kw in ("非理性炒作", "击鼓传花", "炒作情绪过热", "受市场情绪过热影响"):
        m = re.search(rf"([^。\n]{{0,150}}{kw}[^。\n]{{0,150}}。)", t)
        if m:
            return re.sub(r"\s+", " ", m.group(1))[:400]
    for kw in ("过热", "换手率", "市盈率", "涨幅偏离"):
        m = re.search(rf"([^。\n]{{0,150}}{kw}[^。\n]{{0,180}}。)", t)
        if m:
            return re.sub(r"\s+", " ", m.group(1))[:400]
    m = re.search(r"(特别提示|风险提示)[：:\n]?(.{0,500})", t, re.S)
    if m:
        return re.sub(r"\s+", " ", m.group(0))[:400]
    for kw in ("基本面无", "理性投资", "理性决策", "风险"):
        m2 = re.search(rf"([^。\n]{{0,120}}{kw}[^。\n]{{0,200}}。)", t)
        if m2:
            return re.sub(r"\s+", " ", m2.group(1))[:400]
    return ""


def classify(title, text, yidong_month_count):
    blob = (title or "") + "\n" + (text or "")
    quote = extract_quote(text, title)
    for pat, why in STRONG:
        if pat in blob:
            return "🔴", f"公告{why}", quote
    if ("异常波动" in (title or "")) and yidong_month_count >= 3:
        return "🔴", f"一月内第{yidong_month_count}次异常波动公告+涨幅换手异常披露", quote
    weak = []
    if "基本面未发生重大变化" in blob or "基本面无重大变化" in blob or "基本面无变化" in blob:
        weak.append("公告称「基本面无重大变化」")
    if blob.count("理性决策") + blob.count("理性投资") >= 2:
        weak.append("公告复述「理性投资/理性决策」≥2次")
    if "市盈率为负" in blob or "市盈率为负数" in blob:
        weak.append("滚动PE为负")
    if "过热" in blob or "换手率" in blob:
        weak.append("公告提示换手率显著高于日常水平/交易过热风险")
    if "关注函" in (title or ""):
        weak.append("交易所关注函")
    if "问询函" in (title or ""):
        weak.append("交易所问询函")
    if "业绩亏损" in blob or "亏损" in blob:
        weak.append("业绩亏损表述")
    if any(k in (title or "") for k in ("风险提示", "异常波动")):
        weak.append("风险提示/异常波动公告")
    if weak:
        return "🟠", "；".join(dict.fromkeys(weak)), quote
    return "🟡", "常规披露", quote


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("codes", nargs="+")
    ap.add_argument("--days", type=int, default=5)
    ap.add_argument("--month", type=int, default=35)
    ap.add_argument("--date", default=dt.date.today().strftime("%Y%m%d"))
    ap.add_argument("--pdf-per-stock", type=int, default=3)
    a = ap.parse_args()
    d0 = dt.datetime.strptime(a.date, "%Y%m%d").date()
    start = (d0 - dt.timedelta(days=a.days)).strftime("%Y-%m-%d")
    end = d0.strftime("%Y-%m-%d")
    mstart = (d0 - dt.timedelta(days=a.month)).strftime("%Y-%m-%d")

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
        # 一月内异动公告次数
        ycount = 0
        try:
            ym = query(code, oid, mstart, end)
            ycount = sum(1 for x in ym if "异常波动" in (x.get("announcementTitle") or ""))
        except Exception:
            pass
        anns = sorted(anns, key=lambda x: pub_date(x), reverse=True)
        rec = {"code": code, "orgId": oid, "total": len(anns),
               "month_yidong_count": ycount,
               "titles": [f"{pub_date(x)} {x.get('announcementTitle')}" for x in anns][:20],
               "hits": []}
        keys = ("异常波动", "风险提示", "关注函", "问询函", "立案", "处罚")
        hits = [x for x in anns if any(k in (x.get("announcementTitle") or "") for k in keys)]
        for i, x in enumerate(hits[:a.pdf_per_stock]):
            title = x.get("announcementTitle") or ""
            try:
                txt = pdf_text(x.get("adjunctUrl") or "")
            except Exception as e:
                txt = f"[PDF失败 {e}]"
            lvl, why, quote = classify(title, txt, ycount)
            rec["hits"].append({"date": pub_date(x), "title": title, "level": lvl,
                                "reason": why, "quote": quote,
                                "pdf": os.path.basename(x.get("adjunctUrl") or ""),
                                "pdf_ok": not txt.startswith("[")})
        result.append(rec)
        print(f"[{code}] 5日公告{len(anns)}条 / 一月异动{ycount}次 / 命中{len(hits)}", flush=True)
        for h in rec["hits"]:
            print(f"    {h['level']} {h['date']} {h['title']} | {h['reason']} | {h['quote'][:180]}", flush=True)

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"cninfo_{a.date}.json")
    json.dump(result, open(path, "w"), ensure_ascii=False, indent=1)
    print("SAVED", path)


if __name__ == "__main__":
    main()
