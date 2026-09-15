---
name: duanxianxia-pool
version: "1.0.0"
description: |
  短线侠股票池维护（3天3板池）与梯队角色标注：build 重建股票池 / show 查看 / check 主线持续提醒 /
  roles 梯队角色（连板/断板/分歧/观察 + 昨日量能）写入 ~/.cache/duanxianxia/pool.json，供次日盘前读取。
  含同概念比选规则（连板>断板>连续分歧；唯一连板+昨日放量=概念温度计）。脚本 scripts/pool_builder.py
  仅依赖 requests、内置 ≥10 秒限流防整站 403。
  使用时机（即使未明说也应触发）：盘后 18:50 池维护（深查第一步）、盘前取池内最强票、
  用户问「股票池 / 梯队角色 / roles / 主线持续提醒」时。
origin: custom (duanxianxia 子技能, 2026-09-16 拆分)
---

# duanxianxia-pool 股票池维护

> 数据底座（端点全表/免费通道/token）见 `~/.claude/skills/duanxianxia/SKILL.md`；负面提醒见 `duanxianxia-health`。

## 一、建池规则

1. 过去 5 个交易日内出现「X天X板」（X≥3，连续板）的股票 → 加入**股票池**；
2. 池内股票的涨停概念标签 → 作为**主线关注列表**；
3. 每个交易日收盘后检查：池内个股 / 主线概念是否**持续有涨停、连板** → 输出「⚠️ 主线持续提醒」（放复盘报告开头）。

## 二、脚本与命令

脚本：`~/.claude/skills/duanxianxia/scripts/pool_builder.py`（仅依赖 requests，走免费复盘 API；`_throttle` ≥10 秒防整站 403）

```bash
python3 ~/.claude/skills/duanxianxia/scripts/pool_builder.py build            # 重建股票池（默认近5个交易日，含X天Y板非连续）
python3 ~/.claude/skills/duanxianxia/scripts/pool_builder.py show             # 查看股票池与高频概念
python3 ~/.claude/skills/duanxianxia/scripts/pool_builder.py check [--date YYYYMMDD]   # 当日主线持续提醒
python3 ~/.claude/skills/duanxianxia/scripts/pool_builder.py roles [--date YYYYMMDD]   # 梯队角色=连板/断板/分歧/观察+昨日量能，写 pool.json
```

## 三、状态文件（跨 opencode / Hermes 共享）

`~/.cache/duanxianxia/pool.json`：

| 字段 | 写入方 | 说明 |
|---|---|---|
| `stocks` | build | 池内股票（代码/名称/概念/X天Y板） |
| `roles` / `roles_date` | roles | 梯队角色标注，供次日竞价读取；`roles_date` 非昨日 → 9:27 竞价前现场补跑 |
| `warnings` | duanxianxia-health | 负面提醒（只提醒不拉黑）：{code或概念: {level:"🔴"/"🟠", reason, date, quote}} |

## 四、判定与输出

- 【池内个股续板】池内股票今日继续涨停（列出几板）；
- 【主线概念持续】池内概念今日匹配到 ≥2 只涨停，或出现连板；
- 无延续 → `✅ 池内个股与主线概念今日无涨停/连板延续`。
- ⚠️ roles 展示分组曾出现「6只连板」对不上的问题——写报告前必须逐票核 roles 数据。

## 五、同概念/板块内比选（关注池 >10 只时必做）

- **组内排序**：连板 > 断板 > 连续分歧；连板=主线资金共识，断板=博弈修复弹性，连续分歧=资金涣散只观察。
- **唯一连板+昨日放量 → 双向预案**：热点回流（竞价承接强/未匹配>0/温和高开）= 概念内首选可半路打板；分歧（竞价跳水/未匹配转负/低开）→ 观察断板弱转强卡位。
- **温度计逻辑**：所有概念横向比较，优先看「唯一连板+放量」票的竞价走势——它强概念可做，它弱概念降级。

## 六、集成（2026-09-16 拆分后的定时任务）

- **18:50 盘后深查**（第一步）：`build` → `roles --date 今天`；fupan 未更新（解析 0 只）标注「待补算」。
- **9:27 竞价计划**：先 `show`，取池内最强 5 只及其主线概念纳入竞价关注池（roles 缺失时补跑 `roles --date 昨日`）。
- **19:10 复盘汇总**：读取 roles 完成梯队角色表。

## 七、数据源兜底（fupan 未更新时）

fupan 未更新（roles 解析 0 只「待补算」）时，用底座 9.11 选股通接口兜底当日涨停清单并交叉校验（免 token）：
`surge_stock/stocks` 的 `m_days_n_boards`（几天几板）+ `plates`（概念标签）+ `description`（涨停原因原文）。
