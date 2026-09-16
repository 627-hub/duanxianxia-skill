#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""东财：龙虎榜（含席位）+ 个股资金流（新浪源）
实测要点（2026-09-16）:
  - 龙虎榜 reportName=RPT_DAILYBILLBOARD_DETAILS（带 NEW 报 9501「NET_BUY_AMT排序列不存在」）
  - 资金流 push2his 连续取数即断连，已弃用；改用新浪 MoneyFlow（免 token、全历史日序列）
用法: python3 eastmoney_health.py 000993 605058 --date 20260916
"""
import argparse
import json
import os
import time
import urllib.parse
import urllib.request
import datetime as dt

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
OUT = os.path.expanduser("~/.cache/duanxianxia")
_last = [0.0]


def throttle(sec=3.2):
    w = sec - (time.time() - _last[0])
    if w > 0:
        time.sleep(w)
    _last[0] = time.time()


def get(url, referer="https://data.eastmoney.com/", timeout=30, retries=3):
    last = None
    for i in range(retries):
        try:
            throttle()
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer})
            return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore"))
        except Exception as e:
            last = e
            time.sleep(2 * (i + 1))
    raise last


def moneyflow(code, days=8):
    """个股资金流（新浪 MoneyFlow：免 token、全历史日序列；push2his 已弃用）"""
    if code.startswith(("0", "2", "3")):
        pre = "sz"
    elif code.startswith(("4", "8")):
        pre = "bj"
    else:
        pre = "sh"
    url = ("https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
           f"MoneyFlow.ssl_qsfx_zjlrqs?daima={pre}{code}")
    try:
        rows = get(url, referer="https://finance.sina.com.cn/", timeout=20)
        return [{"date": x.get("opendate"),
                 "net": float(x.get("netamount") or 0),
                 "r0_net": float(x.get("r0_net") or 0),
                 "close": x.get("trade"),
                 "chg": x.get("changeratio")} for x in rows[:days]]
    except Exception as e:
        return [{"error": f"{type(e).__name__} {e}"}]


def lhb_day(date):
    """当日龙虎榜全市场 -> {code: row}"""
    flt = urllib.parse.quote(f"(TRADE_DATE='{date}')")
    url = ("https://datacenter-web.eastmoney.com/api/data/v1/get?"
           "reportName=RPT_DAILYBILLBOARD_DETAILS&columns=ALL&source=WEB&client=WEB"
           f"&pageNumber=1&pageSize=500&filter={flt}&sortColumns=BILLBOARD_DEAL_AMT&sortTypes=-1")
    j = get(url)
    rows = (j.get("result") or {}).get("data") or []
    return {r.get("SECURITY_CODE"): r for r in rows}


def lhb_seats(date, code):
    out = {"buy": [], "sell": []}
    for tag, rep in (("buy", "RPT_BILLBOARD_DAILYDETAILSBUY"), ("sell", "RPT_BILLBOARD_DAILYDETAILSSELLS")):
        flt = urllib.parse.quote(f'(TRADE_DATE=\'{date}\')(SECURITY_CODE="{code}")')
        url = ("https://datacenter-web.eastmoney.com/api/data/v1/get?"
               f"reportName={rep}&columns=ALL&source=WEB&client=WEB&pageNumber=1&pageSize=60&filter={flt}")
        try:
            j = get(url)
            out[tag] = (j.get("result") or {}).get("data") or []
        except Exception as e:
            out[tag + "_error"] = f"{type(e).__name__} {e}"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("codes", nargs="+")
    ap.add_argument("--date", default=dt.date.today().strftime("%Y%m%d"))
    a = ap.parse_args()
    date = f"{a.date[:4]}-{a.date[4:6]}-{a.date[6:]}"
    try:
        board = lhb_day(date)
    except Exception as e:
        print(f"[龙虎榜] {date} 获取失败 {e}", flush=True)
        board = {}
    print(f"[龙虎榜] {date} 全市场 {len(board)} 只", flush=True)
    if not board:
        # 找最近有数据的交易日
        d = dt.datetime.strptime(a.date, "%Y%m%d").date()
        for i in range(1, 5):
            dd = (d - dt.timedelta(days=i)).strftime("%Y-%m-%d")
            try:
                b = lhb_day(dd)
                print(f"    回退检查 {dd}: {len(b)} 只", flush=True)
                if b:
                    break
            except Exception as e:
                print(f"    回退检查 {dd}: ERR {e}", flush=True)

    result = []
    for code in a.codes:
        rec = {"code": code, "on_board": code in board}
        row = board.get(code)
        if row:
            rec["board"] = {k: row.get(k) for k in
                            ("SECURITY_NAME_ABBR", "CHANGE_RATE", "BILLBOARD_DEAL_AMT",
                             "BILLBOARD_NET_AMT", "BILLBOARD_BUY_AMT", "BILLBOARD_SELL_AMT",
                             "ACCUM_AMOUNT", "EXPLAIN", "DEAL_AMOUNT_RATIO")}
        seats = lhb_seats(date, code) if row else {"buy": [], "sell": []}
        b, s = seats.get("buy") or [], seats.get("sell") or []
        rec["buy_seats"] = [{"dept": x.get("OPERATEDEPT_NAME"), "buy": x.get("BUY"), "sell": x.get("SELL")} for x in b]
        rec["sell_seats"] = [{"dept": x.get("OPERATEDEPT_NAME"), "buy": x.get("BUY"), "sell": x.get("SELL")} for x in s]
        tot = sum(float(x.get("BUY") or 0) for x in b) or 0
        em = [x for x in b if "东方财富" in (x.get("OPERATEDEPT_NAME") or "")]
        em_amt = sum(float(x.get("BUY") or 0) for x in em)
        rec["em_buy_count"] = len(em)
        rec["em_buy_ratio"] = round(em_amt / tot, 3) if tot else None
        rec["retail_takeover"] = bool(len(em) >= 2 and tot and em_amt / tot > 0.30)
        rec["mf"] = moneyflow(code)
        result.append(rec)
        print(f"[{code}] 上榜={rec['on_board']} 东财买方{len(em)}家 占比{rec['em_buy_ratio']} 散户接盘={rec['retail_takeover']}", flush=True)
        for x in rec["buy_seats"][:6]:
            print("    买:", x["dept"], x["buy"], flush=True)
        for x in rec["sell_seats"][:6]:
            print("    卖:", x["dept"], x["sell"], flush=True)
        for k in rec["mf"][-4:]:
            print("    资金:", k, flush=True)

    path = os.path.join(OUT, f"eastmoney_{a.date}.json")
    json.dump(result, open(path, "w"), ensure_ascii=False, indent=1)
    print("SAVED", path)


if __name__ == "__main__":
    main()
