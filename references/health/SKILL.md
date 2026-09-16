---
name: duanxianxia-health
version: "1.0.0"
description: |
  短线侠公告/梯队健康度深查（只提醒不拉黑）。两模式：
  ①盘后深查（18:50）：对同概念≥2只的梯队概念连板票做三项检查——异常波动公告三级判定（巨潮，原文引用）、
  龙虎榜席位（东财，散户接盘/对倒）、资金流出；
  ②盘前隔夜扫描（8:30）：巨潮扫昨夜 18:00→今早 08:30 新公告（异常波动/风险提示/关注函/问询函/立案/处罚）三级判定。
  结论写 ~/.cache/duanxianxia/pool.json 的 warnings 字段 + 明细写 health_YYYY-MM-DD.json；票永不剔除、不做禁止性处理。
  使用时机（即使未明说也应触发）：盘后深查、8:30 盘前公告扫描、公告排雷、查看/更新负面提醒、用户问「warnings」时。
origin: custom (duanxianxia 子技能, 2026-09-16 拆分)
---

# duanxianxia-health 公告/梯队健康度

> 数据底座见 `~/.claude/skills/duanxianxia/SKILL.md`；池与 roles 读取见 `duanxianxia-pool`。

## 一、只提醒不拉黑（用户定稿 2026-09-15）

- 结论写 `~/.cache/duanxianxia/pool.json` 的 `warnings` 字段：
  `{code或概念: {level: "🔴"/"🟠", reason: "...", date: "YYYY-MM-DD", quote: "公告原文关键句"}}`
- **票永不剔除**——次日盘前只读 warnings，在关注池表格旁加 🔴/🟠 标记 + 一句风险摘要；
- 参与与仓位由用户自决，不做任何禁止性处理（不设禁止、不强制降仓）。
- 盘后深查的逐概念明细另写 `~/.cache/duanxianxia/health_YYYY-MM-DD.json`
  （字段：`[{概念, 公告级, 原文关键句, 龙虎榜, 资金, 结论}]`，供 19:10 复盘 JSON 的「梯队健康度」字段）。

## 二、公告三级判定（两模式共用）

1. **🔴 强负面**（公司直接打击炒作情绪）：「击鼓传花」字样 / 「炒作情绪过热」「非理性炒作」「勿受市场情绪过热影响」/ 一月内第 3 次及以上异动+涨幅换手异常披露——公告原文**必须引用**进报告；这类公告次日通常低开。
2. **🟠 弱负面**：滚动PE亏损 / 业绩亏损 / 扣非<−50% / PE/PB远高于行业（估值偏离类只算弱负面——未直接打击炒作情绪，公告次日走势不确定，竞价照常判定）/「基本面无变化」/「理性决策」复述≥2次。
3. **🟡 中性**：常规披露。关注函/问询函 → 至少弱负面，叠加情绪定性则强负面。

## 三、盘后深查模式（18:50）

触发：同概念 ≥2 只的梯队概念，对其**连板票**批量三项检查：

1. **异常波动公告三级判定**（巨潮 hisAnnouncement + pdftotext，抓「特别提示」段）；
2. **龙虎榜席位**（东财 datacenter，请求间隔 ≥3 秒）：买方东财席位 ≥2 家且占比 >30% = 散户接盘；净买连续负而连板 = 对倒嫌疑；东财断连/限流时降级用交易所官方源（深交所/上交所，见 三.1）；
3. **资金流出**（连板但主力持续净流出 = 借情绪出货）——数据源优先级（2026-09-16 实测定稿）：
   - **默认主源：新浪个股资金流趋势**（免费、免 token、历史日序列）：
     ```python
     GET https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/MoneyFlow.ssl_qsfx_zjlrqs?daima=sz000993
     # → [{opendate, trade, changeratio, turnover, netamount(净流入额,元), ratioamount(净流入占比),
     #     r0_net(特大单净额,元), r0_ratio(特大单净占比), r0x_ratio, ...}, ...]  最新在前，全历史
     ```
     连续多日 `r0_net` / `netamount` 为负 = 持续净流出；间隔 ≥1 秒（实测可连续调用）；
   - 交叉验证：龙虎榜净买卖额（东财 datacenter，与席位检查同批）；
   - 应急单发：东财 push2 `stock/get`（同族 push2his 连续即断连，不可批量）；
   - 已失效/不可用：腾讯 `ff_`、ifzq `ffqs`（接口下线）；百度股市通（Result null）；tdx `symbol_zjlx`（schema 校验失败）。

限流与时间预算：新浪 ≥1 秒；东财 datacenter ≥3 秒；巨潮 ≥1 秒；PDF 每票 1 份；单概念 ≤90 秒；**深查总时长 ≤15 分钟（19:05 前完成落盘），保证 19:10 复盘可用——取数失败一律降级标注，不追数据**。结论合并写入 warnings（与昨夜 warnings 合并，保留 `quote` 原文）。

### 三.1 脚本与接口实测要点（2026-09-16 固化，踩坑必读）

脚本：`scripts/cninfo_health.py`（巨潮公告三级判定）、`scripts/eastmoney_health.py`（龙虎榜席位 + 资金流）

```bash
/opt/homebrew/bin/python3 ~/.claude/skills/duanxianxia/references/health/scripts/cninfo_health.py 000993 605058 --days 5 --date YYYYMMDD
/opt/homebrew/bin/python3 ~/.claude/skills/duanxianxia/references/health/scripts/eastmoney_health.py 000993 605058 --date YYYYMMDD
```

- **解释器**：必须 `/opt/homebrew/bin/python3`——系统 `python3`/`/usr/bin/python3` 无 requests（实测 ModuleNotFoundError）。
- **巨潮**：`hisAnnouncement/query` 的 `column` **固定 `szse`**；传 `shse` 对沪市票**静默返回 0 条**（会漏报 605xxx 的风险提示公告）。`stock=代码,orgId`，orgId 取自 `/new/data/szse_stock.json`（含沪深全量 6254 条）。PDF 取 `http://static.cninfo.com.cn/<adjunctUrl>`，用 `pdftotext -layout` 后正则抓**整句**「非理性炒作/击鼓传花/过热/换手率/市盈率」——只抓「特别提示」段会漏掉关键定性句。
- **东财龙虎榜**：`reportName=RPT_DAILYBILLBOARD_DETAILS`（**带 `NEW` 会报 `9501 NET_BUY_AMT 排序列不存在`**）；买方席位 `RPT_BILLBOARD_DAILYDETAILSBUY`、卖方席位 `RPT_BILLBOARD_DAILYDETAILSSELL`（**`...SELLS` 报表不存在**，写错返回空且不报错）。买方表同时含 BUY/SELL 双向金额，可识别同一席位对倒。当日榜 18:50 前已可查。
- **龙虎榜降级（东财限流/断连时用，2026-09-16 实测全通）**——交易所官方零鉴权一手源，需带浏览器 UA + Referer：
  ```python
  # 深交所（JSON，日期必须连字符；PAGENO 翻页，每页 10 条直到空）
  GET https://www.szse.cn/api/report/ShowReport/data?SHOWTYPE=JSON&CATALOGID=1842_xxpl&TABKEY=tab1
       &txtStart=YYYY-MM-DD&txtEnd=YYYY-MM-DD&PAGENO=1
  #   Referer: https://www.szse.cn/disclosure/supervision/dealinfo/index.html
  #   → data[]: zqdm/zqjc/cjje(万元)/cjsl/plyy(上榜原因)/bz(含席位明细参数 DQRQ、ZQDM、ZBDM)
  # 深交所席位明细（参数取自榜单 bz 字段）：
  GET https://www.szse.cn/api/report/ShowReport/data?SHOWTYPE=JSON&CATALOGID=1842_detal
       &TABKEY=tab1,tab2&DQRQ=YYYY-MM-DD&ZQDM=代码&ZBDM=0901
  #   → tab1: mmlb(买1/卖1…)/zsmc(营业部)/mrje(买入,元)/mcje(卖出,元)
  # 上交所（JSONP，返回 fileContents 文本块＝每日交易信息全文含席位段，需文本解析）：
  GET https://query.sse.com.cn/infodisplay/showTradePublicFile.do?jsonCallBack=cb&isPagination=false&dateTx=YYYY-MM-DD
  #   Referer: https://www.sse.com.cn/disclosure/diclosure/public/
  ```
  降级链：**东财 datacenter（主）→ 深交所 1842_xxpl/1842_detal（深市，JSON）+ 上交所 showTradePublicFile（沪市，文本）**；深交所数据与东财交叉核对过一致（002585 深股通买 1.695 亿）。
- **资金流**：push2his 连续取数即断连、**已弃用**——统一用新浪 MoneyFlow（见第三节第 3 条数据源优先级）；`eastmoney_health.py` 的 `moneyflow()` 已切到新浪源。
- 散户接盘口径：沪市「东方财富证券…拉萨…营业部」；**买方东财席位 ≥2 家且占买方总额 >30%** 才算（单家不算）。
- 深查结论落盘后**回读校验**（roles 键与 stocks 一致、warnings 条数），并在 19:10 前完成——19:10 复盘任务依赖 `health_YYYY-MM-DD.json`。

## 四、盘前隔夜扫描模式（8:30）

> 前置：先跑 `python3 ~/.claude/skills/duanxianxia/scripts/trade_day.py` —— 输出以 NO 开头 = 非交易日 → 直接结束、不输出；UNKNOWN（日历源不可用）→ 按交易日继续并注明「交易日历未校验」。

1. 读 `pool.json`：池内全部股票代码 + 现有 warnings；
2. 逐票扫隔夜公告（昨晚 18:00 → 今早 08:30 新发布）：巨潮 hisAnnouncement/query（orgId 用官方映射表 `http://www.cninfo.com.cn/new/data/szse_stock.json`，**`column` 固定填 `szse`——填 `shse` 或按交易所分支会让沪市票静默返回 0 条**），seDate 设为 昨日18:00~今天08:30，searchkey 依次查「异常波动」「风险提示」「关注函」「问询函」「立案」「处罚」；无命中则跳过该票；请求间隔 ≥1 秒；每票公告列表最多 10 条；单票 PDF 最多 1 份（最新）；总耗时 ≤6 分钟（8:30-8:36），超时对未扫描票标注「未及扫描，开盘前人工留意」；
3. 命中公告按第二节三级判定，合并写回 warnings；
4. 输出报告（500字内，简体中文）：
   - 无新增：`✅ 隔夜公告核查完毕，池内N只无新增负面（现有负面提醒：XX🔴/XX🟠），可按今早9:26竞价计划执行。`
   - 有新增：①新增负面列表（代码|名称|公告类型|风险级🔴/🟠|原文关键句）②提醒汇总：「⚠️今日负面提醒（仅供参考，自行决策）：XX(🔴…)、XX(🟠…)」③已更新 warnings。

## 五、连续一字加速票（原 12.2 补充）

- 连续一字加速票**不接加速**：高开不参与、一字只排不追、分歧充分（竞价放量未匹配转负再转正、或开盘充分换手）才低吸试仓且仓位减半 ≤8%，破前日涨停价止损；冰点期连续一字票一律只观察。
