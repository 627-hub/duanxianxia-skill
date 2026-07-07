---
name: duanxianxia
description: 短线侠(duanxianxia.cn)全功能数据工具包 — 覆盖涨停播报、竞价异动、板块强度、资金流向、龙虎榜、连板天梯、情绪指标、个股异动解析、题材库等30+数据端点。支持盘中/盘后数据采集，部分端点含fupan复盘JSON API。适用于打板跟踪、情绪量化、板块轮动、个股挖掘、复盘分析等场景。
origin: custom
version: 1.0.0
---

> 站点：https://duanxianxia.cn — 短线侠，专注短线情绪与涨停数据

# 短线侠数据工具包 V1.0.0

**共用参数：** 所有端点均需 `{token}` 标识用户身份（示例值 `<YOUR_TOKEN>`）。  
**基域名：** `duanxianxia.cn`（HTML页面），`duanxianxia.com`（JSON复盘API）。  
**返回格式：** 绝大多数端点为**服务端渲染HTML**，需用HTML解析提取数据；fupan系列为JSON。

## 一、涨停/连板/晋级

### 1.1 涨停播报（实时）
#### HTML版（需token）
```
ZT_LIVE = "https://duanxianxia.cn/web/ztlive/{token}/light"
```
实时涨停股票列表。包含名称、代码、涨幅、状态(首板/炸板)、首封时间、封单金额、板块/概念。数据随盘面实时更新。

#### JSON API版（无需token，推荐）
```
ZT_LIVE_JSON = "https://duanxianxia.cn/vendor/livedata/ztlive.json"
```
纯JSON格式，`Content-Type: application/json`。返回 `{"result":"success","list":[...]}`，每项含 `code, name, ztyy(涨停原因), zt(涨停类型/板数), time`。无需token，但有频率限制（连续请求间隔建议 ≥ 10秒）。

### 1.2 股票池（综合）
```
POOL = "https://duanxianxia.cn/web/pool/{token}"
```
多维度股票池聚合：涨停、连板、封板率、炸板、冲涨、热门、大面、跌停。每只股票含板数、首封、封单、成交额、实际流通、概念。

### 1.3 涨停晋级
```
JINJI = "https://duanxianxia.cn/web/jinji/{token}"
```
涨停晋级率与晋级股票池。

### 1.4 连板天梯
```
LIANBAN = "https://duanxianxia.cn/web/lianban/{token}"
```
各连板层级的股票分布（首板/2板/3板/.../高位板）。

### 1.5 龙头高度
```
LTGD = "https://duanxianxia.cn/web/ltgd/{token}"
```
市场最高连板标的及高度追踪。

### 1.6 历史涨停今表现
```
ZT_HISTORY = "https://duanxianxia.cn/web/zthis/{token}"
```
昨日涨停股票今日的表现统计（溢价/亏钱效应）。

## 二、竞价/盘口

### 2.1 竞价异动
```
JJYD = "https://duanxianxia.cn/mob/jjyd/{token}"
```
分 tab 展示：涨停委买、昨日涨停、竞价爆量、竞价抢筹、竞价净额、昨炸板、昨断板、昨上榜。每只股票含竞价换手、竞涨、主力净买、竞额、竞价量比等。

### 2.2 竞价封单对比
```
JJ_LIVE = "https://duanxianxia.cn/web/jjlive/{token}"
```
盘前竞价时段封单金额与竞价量对比。

### 2.3 竞价承接强度对比
```
JINGJIA = "https://duanxianxia.cn/web/jingjia/{token}"
```
竞价承接力度排序，含竞涨、竞额、竞量比等指标。

### 2.4 盘口异动播报
```
YIDONG_BOBAO = "https://duanxianxia.cn/web/yidong/{token}"
```
盘中逐笔异动播报（大单扫货、砸盘等盘口信号）。

## 三、板块/行业

### 3.1 实时板块强度
```
STRONG = "https://duanxianxia.cn/stock/strong/{token}/light"
```
按板块聚合个股强度，含板块强度值、主力净额、涨幅、涨停家数。点击板块可展开个股列表（名称、代码、涨幅、成交、换手、流通、板数、主力净额、竞价数据、封单等）。

### 3.2 板块轮动
```
PLATE_ROTATE = "https://duanxianxia.cn/web/platerotat/{token}"
```
板块轮动节奏图，可选近10/20/30/50日板块强度与量能趋势。支持开盘啦板块与同花顺板块分类。

## 四、资金/量能

### 4.1 沪深量能
```
AMOUNT = "https://duanxianxia.cn/web/amount/{token}"
```
今日量能、预测量能、昨日量能。适合判断大盘活跃度。

### 4.2 沪深主力资金流向
```
FUND = "https://duanxianxia.cn/stock/fund/{token}"
```
主力资金（超大单/大单）与北向资金流向。

### 4.3 个股分时大单
```
MONEY = "https://duanxianxia.cn/web/money/{token}/{code}"
```
个股分时大单成交明细（逐笔大单追踪）。

### 4.4 个股资金博弈
```
ZHULI = "https://duanxianxia.cn/web/zhuli/{token}/{code}"
```
个股主力/散户资金博弈可视化。

## 五、情绪/复盘

### 5.1 市场情绪概览
```
QIXIN = "https://duanxianxia.cn/web/qxlive/{token}"
```
市场综合情绪仪表盘：情绪指标、涨停家数、跌停家数、亏钱效应、主力流入、连板高度、上涨/下跌家数、封板率、昨涨停表现、昨连板表现、沪深5分钟量能。

### 5.2 市场情绪（精简版）
```
QIXIN_SIMPLE = "https://duanxianxia.cn/web/qxlive/{token}/black/simple"
```
精简版情绪面板，含板块强度与主力流入排名。

### 5.3 每日复盘（纯数据版）
```
FUPAN_GU = "https://duanxianxia.cn/web/fupangu/{token}"
```
每日复盘报告。

### 5.4 复盘日期查询 (JSON API)
```
FUPAN_DATE_API = "https://duanxianxia.com/api/getFupanDate"
```
POST 请求。参数：`date=YYYYMMDD`、`type=prev|next|choose`。  
返回 `{"result":"success","date":"YYYY-MM-DD"}`。用于确认交易日、前后导航。

### 5.5 复盘异动分组数据 (JSON API)
```
FUPAN_YIDONG_API = "https://duanxianxia.com/api/getFupanByYidong"
```
POST 请求。参数：`date=YYYYMMDD`、`type=plate`。  
返回 `{"result":"success","html":...,"htmlcopy":"..."}`。`htmlcopy` 包含纯文本格式的涨停复盘数据：情绪指标、涨停家数、跌停家数、封板率、涨停表现、连板表现。`html` 为分概念板块的涨停分组数据（含连板数、异动原因等）。

### 5.6 个股异动解析
```
YIDONG = "https://duanxianxia.cn/stock/yidong/{token}/{code}"
```
目标股票的历史异动原因详细解析。含涨停日期、概念匹配、异动原因完整文本（基本面/消息面驱动逻辑）。

### 5.7 异动解析（同花顺版）
```
THSYD = "https://duanxianxia.cn/stock/thsyd/{token}/{code}"
```
同花顺风格个股异动解析。

## 六、个股挖掘/信息

### 6.1 综合挖掘
```
WAJUE = "https://duanxianxia.cn/web/wajue/{token}"
```
多维度挖掘：同花概念匹配、历史异动、主营业务、申万行业、互动易、研报。支持按板块（全部/主板/创业板/科创/北交）和关键词搜索。含涨幅、流通市值、近1年涨停次数等筛选。

### 6.2 股票基本信息联动
```
SHOW_BASIC = "https://duanxianxia.cn/stock/showbasic/{token}/{code}"
```
个股基本信息：公司亮点、主营业务、概念排名（含BK码）、申万行业、对标公司。适合快速了解标的定位。

### 6.3 同概念个股联动
```
SIMILAR = "https://duanxianxia.cn/stock/similar/{token}/{code}"
```
同概念股票列表：展示同板块内的其他股票，含涨幅、流通市值、概念匹配度。

### 6.4 题材库
```
TCK = "https://duanxianxia.cn/web/tck/{token}"
```
题材概念分类库，可按题材浏览个股。

### 6.5 互动易挖掘
```
HUDONG = "https://duanxianxia.cn/stock/hudong/{token}"
```
互动易平台的公司回复/投资者问答挖掘，可按关键词搜索。

### 6.6 溢价基因
```
YJJY = "https://duanxianxia.cn/web/yjjy/{token}/{code}"
```
个股涨停溢价基因分析（历史涨停后的溢价表现统计）。

### 6.7 个股人气趋势
```
DCRANK = "https://duanxianxia.cn/web/dcrank/{token}/{code}"
```
个股在平台的人气趋势（1小时/24小时热度排名变化）。

## 七、龙虎榜/其他

### 7.1 龙虎榜
```
LONGHU = "https://duanxianxia.cn/web/longhu/{token}"
```
每日龙虎榜上榜股票及买卖席位数据。

### 7.2 热点聚焦
```
HOT_NEWS = "https://duanxianxia.cn/web/hotnews/{token}/tdx"
```
综合热点资讯聚合：热点资讯、今日热点、公社热帖、同花热榜、财经日历、热股榜、飙升榜、美股、港股、热门话题。

### 7.3 沪深主力资金流向（同4.2）
```
FUND = "https://duanxianxia.cn/stock/fund/{token}"
```
全市场主力资金（超大单/大单）及北向资金实时流向。

## 八、Python 使用示例

```python
import re
import json
import requests
from bs4 import BeautifulSoup

TOKEN = "<YOUR_TOKEN>"
TOKEN2 = "<YOUR_TOKEN2>"

def fetch_zt_live_json():
    \"\"\"获取实时涨停播报 (JSON API, 无需token, 推荐)\"\"\"
    url = "https://duanxianxia.cn/vendor/livedata/ztlive.json"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    return resp.json()["list"]

def fetch_zt_live_html(token=TOKEN):
    \"\"\"获取实时涨停播报 (HTML解析, 需token)\"\"\"
    url = f"https://duanxianxia.cn/web/ztlive/{token}/light"
    resp = requests.get(url, timeout=10)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")
    # 解析表格行, 提取 名称/代码/涨幅/状态/首封/封单/板块
    rows = soup.select("table tr")
    result = []
    for row in rows[1:]:
        cols = row.find_all("td")
        if len(cols) >= 7:
            result.append({
                "name": cols[0].get_text(strip=True),
                "code": cols[1].get_text(strip=True),
                "pct": cols[2].get_text(strip=True),
                "status": cols[3].get_text(strip=True),
                "first_seal": cols[4].get_text(strip=True),
                "seal_amount": cols[5].get_text(strip=True),
                "concept": cols[6].get_text(strip=True),
            })
    return result

def fetch_yidong(code, token=TOKEN):
    \"\"\"获取个股异动解析 (HTML解析)\"\"\"
    url = f"https://duanxianxia.cn/stock/yidong/{token}/{code}"
    resp = requests.get(url, timeout=10)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(separator="\n", strip=True)
    return text

def fetch_show_basic(code, token=TOKEN):
    \"\"\"获取股票基本信息\"\"\"
    url = f"https://duanxianxia.cn/stock/showbasic/{token}/{code}"
    resp = requests.get(url, timeout=10)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(separator="\n", strip=True)
    return text

def fetch_fupan_date(date, direction="choose"):
    \"\"\"查找复盘日期 (JSON API)
    direction: prev-前一天, next-后一天, choose-确认
    \"\"\"
    url = "https://duanxianxia.com/api/getFupanDate"
    resp = requests.post(url, data={"date": date, "type": direction}, timeout=10)
    return resp.json()

def fetch_fupan_yidong(date):
    \"\"\"获取复盘异动分组数据 (JSON API)
    返回包含情绪指标、涨停分组、连板数、概念分类
    \"\"\"
    url = "https://duanxianxia.com/api/getFupanByYidong"
    resp = requests.post(url, data={"date": date, "type": "plate"}, timeout=10)
    return resp.json()
```

## 九、注意事项

1. **HTTP 仅限 `duanxianxia.cn` 与 `duanxianxia.com`**，无 HTTPS 降级问题
2. HTML 端点需配合 `BeautifulSoup` 或正则解析；JSON 端点仅 fupan 相关
3. 页面数据均为**服务端渲染**，无需执行 JavaScript，requests 即可获取
4. `{token}` 为用户身份标识，请勿泄露
5. 数据更新时效：涨停播报/情绪面板为**实时**，竞价异动仅在**竞价时段**(9:15-9:25)有数据
6. 备用token：`<YOUR_TOKEN2>`（主token `<YOUR_TOKEN>` 失效时切换）
7. `ztlive.json` 无需token但有频率限制，连续请求间隔建议 ≥ 10秒，否则返回 403
8. 盘中数据请求频率建议 ≤ 1次/秒，避免被限制
9. 已对接的现有脚本：`fetch_daily_zt.py`（使用 `fupan_date` + `fupan_yidong` API 获取历史涨停数据）
