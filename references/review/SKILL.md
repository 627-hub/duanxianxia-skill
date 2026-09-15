---
name: duanxianxia-review
version: "1.0.0"
description: |
  盘后复盘汇总与推送（19:10）：情绪周期信号（顶点→降仓 / 冰点→建仓 / 回暖→加仓，含 check_sentiment_signal 实现）、
  亏钱效应与板块分歧检验、题材持续性监控（宽度↑/负反馈↓/断线）、复盘报告结构（推送摘要①~⑤ + 完整JSON字段）。
  汇总上游环节：duanxianxia-health 的 warnings、duanxianxia-verify 的「竞价计划验证」，只发结论摘要 400-600 字。
  使用时机（即使未明说也应触发）：盘后复盘、情绪信号判断、题材持续性表、复盘报告/JSON 生成、用户问「今天复盘」时。
origin: custom (duanxianxia 子技能, 2026-09-16 拆分)
---

# duanxianxia-review 盘后复盘汇总

> 上游数据流：pool（roles）→ health（warnings + health_YYYY-MM-DD.json 明细）→ verify（竞价计划验证）→ 本 skill 汇总。
> 数据底座（端点全表/免费通道/token）见 `~/.claude/skills/duanxianxia/SKILL.md`。

## 一、情绪周期信号（第10节，盘后必做）

每个交易日盘后复盘时**必须**先跑一次情绪信号检测，并把结论写进复盘输出。阈值可调（代码常量 `PEAK/ICE/WARM`）：

| 信号 | 条件 | 动作 |
|---|---|---|
| ⚠️ 情绪顶点退潮 | 昨日情绪指标 **> 60**，且今日 涨停家数、封板率、赚钱效应（涨停表现或连板表现）**较昨日均下降** | **降仓** |
| 🧊 情绪冰点 | 今日情绪指标 **≤ 35** | **开始分批试探建仓** |
| 🔥 情绪回暖确认 | 今日情绪指标较昨日 **回升 ≥ 5**，且涨停家数回升，且（赚钱效应 或 封板率 回升） | **加仓** |

> 退潮期顶点信号可能连续触发（每天都是有效的降仓提醒）；冰点信号在指标明显回暖前会持续触发。
> 该信号仅为仓位节奏参考，不构成投资建议。

参考实现：

```python
import re
import requests

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.0 Safari/605.1.15")


def _plain(hc):
    t = re.sub(r"<br\s*/?>", "\n", hc)
    t = re.sub(r"</(div|tr|td|table|p|button|span)>", "\n", t)
    t = re.sub(r"<[^>]+>", "", t)
    return "\n".join(re.sub(r"\s+", " ", l).strip() for l in t.split("\n") if l.strip())


def daily_sentiment(date):
    """date=YYYYMMDD -> {qixi, zt, dt, fbl, ztbx, lbbx}"""
    r = requests.post("https://duanxianxia.com/api/getFupanByYidong",
                      data={"date": date, "type": "plate"},
                      headers={"User-Agent": UA}, timeout=20)
    t = _plain(r.json().get("htmlcopy", ""))
    def g(pat):
        m = re.search(pat, t)
        return float(m.group(1)) if m else None
    return {"date": date,
            "qixi": g(r"情绪指标[:：]\s*(\d+)"),
            "zt":   g(r"涨停家数[:：]\s*(\d+)"),
            "dt":   g(r"跌停家数[:：]\s*(\d+)"),
            "fbl":  g(r"封板率[:：]\s*([\d.]+)%"),
            "ztbx": g(r"涨停表现[:：]\s*([\-+\d.]+)%"),
            "lbbx": g(r"连板表现[:：]\s*([\-+\d.]+)%")}


def prev_trade_date(date):
    """上一交易日 YYYYMMDD（免费 API）"""
    r = requests.post("https://duanxianxia.com/api/getFupanDate",
                      data={"date": date, "type": "prev"},
                      headers={"User-Agent": UA}, timeout=15)
    return (r.json().get("date") or "").replace("-", "")


def check_sentiment_signal(date):
    """盘后情绪信号：顶点→降仓；冰点→分批建仓；回暖→加仓"""
    PEAK, ICE, WARM = 60, 35, 5
    t = daily_sentiment(date)
    y = daily_sentiment(prev_trade_date(date))
    down = lambda a, b: a is not None and b is not None and a < b
    up   = lambda a, b: a is not None and b is not None and a > b
    money_down = down(t["ztbx"], y["ztbx"]) or down(t["lbbx"], y["lbbx"])
    money_up   = up(t["ztbx"], y["ztbx"])   or up(t["lbbx"], y["lbbx"])
    sig = []
    if (y["qixi"] or 0) > PEAK and down(t["zt"], y["zt"]) and down(t["fbl"], y["fbl"]) and money_down:
        sig.append("⚠️ 情绪顶点退潮 → 降仓")
    elif (t["qixi"] or 100) <= ICE:
        sig.append("🧊 情绪冰点 → 分批试探建仓")
    if up(t["qixi"], y["qixi"]) and (t["qixi"] - (y["qixi"] or 0)) >= WARM \
            and up(t["zt"], y["zt"]) and (money_up or up(t["fbl"], y["fbl"])):
        sig.append("🔥 情绪回暖确认 → 加仓")
    return {"today": t, "yesterday": y, "signals": sig}
```

输出示例（2026-09-11 实测）：

```
情绪 33→30 | 涨停 35→40 | 封板率 60.7→69.0 | 溢价 -0.08/-0.45 → 1.03/0.38
信号: 🧊 情绪冰点 → 分批试探建仓
```

## 二、亏钱效应与板块分歧检验（12.3，与涨停情绪并重）

- **亏钱效应数据**：跌停家数、大面票（≤-8%）名单与概念分布、**昨日涨停今日跌停数**（最强亏钱信号）、昨日涨停今日 -5% 以上（炸板分歧回落）。跌停池 getTopicDTPool 常返回空 → 用东财 push2 clist 按涨幅升序取前 30 兜底 + 腾讯批量行情。
- **板块分歧规则（用户定稿 2026-09-15）**：概念**龙头反包涨停但小弟跌停/大面** → ⚠️「板块分歧」**龙头不会有持续性**（龙头独走=资金卡位抱团、板块无合力，次日龙头大概率补跌开板）；反向**昨日反包龙头今日跌停+集体大面=分歧兑现、龙头周期终结**（实证：桂林旅游 9/14 旅游反包→9/15 跌停，天目湖/云南旅游同日 -10%）。命中写 warnings（🟠）。

## 三、题材持续性监控（12.4，盘后必做）

- **题材主键 = fupan htmlcopy 的概念标签**（如 双星新材=MLCC离型膜、中新赛克=数据安全/AI安全），行业字段（hybk/board）**辅助对照**——板块与概念双维度都要考察（用户定稿 2026-09-15）。
- **可选数据源（底座 9.11 选股通，免 token）**：题材「催化/驱动」描述用 `surge_stock/plates`（如"PCB板: 电子布、铜箔及CCL价格持续上行"）补表；个股涨停原因原文用 `surge_stock/stocks` 的 `description`；fupan 缺失时可用其交叉校验今日涨停与几天几板。
- **宽度加宽↑**：题材今日涨停数 ≥ 昨日，或出现二板及以上晋级（首板集体晋级/梯队形成）；连续晋级+新首板=强持续。
- **负反馈↓/断线**：题材昨日涨停标的今日跌停/大面（≤-9.5% 最强负反馈）/炸板回落（≤-5%）→「负反馈堪忧」；昨日有今全无=断线。
- **表格结构**：题材 | 今日涨停数(vs昨日) | 梯队(最高板/二板数/首板数) | 宽度方向(↑/→/↓) | 负反馈(跌停/炸板票) | 结论(强持续/弱持续/负反馈堪忧/断线)。

## 四、复盘报告结构与交付（12.7）

推送摘要段落（400-600字）：
①情绪数据表（涨停+亏钱效应并列）②主线与梯队（题材持续性表+梯队角色表+分歧⚠️标注）③梯队健康度（逐概念公告级/原文关键句/龙虎榜/资金，读 `health_YYYY-MM-DD.json`；缺失时标「深查未完成」）④竞价计划验证（计划 vs 实际，偏差票点名，来自 `duanxianxia-verify`）⑤情绪信号与明日关注（概念温度计；⚠️分歧+负反馈题材明示）。
⚠️负面提醒：来自 pool.json 的 `warnings`（duanxianxia-health 写入），只做信息呈现。

完整 JSON 写 `~/.hermes/cron/output/2aa245c15624/复盘_YYYY-MM-DD.json`（不限字数全量明细）：

```json
{"date": "YYYY-MM-DD",
 "情绪": {"情绪指标": 0, "涨停": 0, "跌停": 0, "封板率": 0, "大面票": []},
 "题材持续性": [{"题材": "", "今日涨停": 0, "昨日涨停": 0, "梯队": "", "宽度方向": "", "负反馈票": [], "结论": ""}],
 "梯队角色表": [{"code": "", "name": "", "角色": "", "高度": "", "概念": "", "今日pct": 0}],
 "板块分歧": [{"概念": "", "龙头": "", "小弟跌停": [], "判定": ""}],
 "梯队健康度": [{"概念": "", "公告级": "", "原文关键句": "", "龙虎榜": "", "资金": "", "结论": ""}],
 "竞价计划验证": [{"票": "", "计划判断": "", "实际走势": "", "偏差类型": "", "教训": ""}],
 "warnings新增": [], "情绪信号": "", "明日关注": ""}
```
