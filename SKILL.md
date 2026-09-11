---
name: duanxianxia
description: 短线侠(duanxianxia.cn)全功能数据工具包 — 覆盖涨停播报、竞价异动、板块强度、资金流向、龙虎榜、连板天梯、情绪指标、个股异动解析、题材库等30+数据端点。支持盘中/盘后数据采集，部分端点含fupan复盘JSON API；内置免 token 免费降级通道（账号过期可用）、盘后情绪信号（情绪顶点→降仓提醒、冰点→建仓提示、回暖→加仓提示）与开盘竞价交易计划（9:25-9:30）。适用于打板跟踪、情绪量化、板块轮动、个股挖掘、复盘分析等场景。
origin: custom
version: 1.3.0
---

> 站点：https://duanxianxia.cn — 短线侠，专注短线情绪与涨停数据

# 短线侠数据工具包 V1.3.0

**共用参数：** 所有端点均需 `{token}` 标识用户身份。本地 token 已存放于 `~/.claude/skills/duanxianxia/.token`（勿提交仓库），使用前读取：
```python
import os
TOKEN = open(os.path.expanduser("~/.claude/skills/duanxianxia/.token")).read().strip()
```
下文所有 `{token}` 占位符均替换为 `TOKEN` 的值。  
**免费降级通道：** 无需 token 的接口清单见第九章（账号过期/额度不足时优先使用）。  
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

TOKEN = open(os.path.expanduser("~/.claude/skills/duanxianxia/.token")).read().strip()

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

## 九、免 Token 免费通道（2026-09 实测可用，账号过期时作为降级）

以下端点**无需 token**，实测全部 200 可用，账号过期/额度不足时优先走这条链路。
通用要求：带**完整浏览器 UA**（短 UA 会被 403）；AJAX 型 JSON 接口建议带 `Referer`/`Origin`/`X-Requested-With`（服务端主要校验 Referer）。

### 9.1 板块轮动
```python
POST https://duanxianxia.com/api/getPlateRotatData
form: from=ths|kaipan, days=20, dates=
Referer: https://duanxianxia.com/web/platerotat/
→ {"first": "首名板块code", "html": "<tr>...（jQuery innerHTML 片段）"}
```
⚠️ 双源语义不同：`ths`（同花顺，88x 代码）= 当日板块涨幅%；`kaipan`（开盘啦，80x/803x）= 强度分。
**不可跨源比较数值，也不可把 88x 的码传给开盘啦接口（反之亦然）。**

### 9.2 板块龙头（龙一~龙N）
```python
POST https://duanxianxia.com/api/getLongByPlate
form: platecode=<9.1 返回的 code>, days=20, dates=
→ {"html": "...（HTML 解析）"}
```

### 9.3 历史涨停池（连板梯队 / 概念分组）
```python
GET  https://duanxianxia.com/web/zthis/iframe          # 先访问，取 Cookie + 最新交易日
POST https://duanxianxia.com/api/getHisZtPool
form: date=YYYYMMDD, type=lianban|plate                 # lianban=连板梯队, plate=概念分组
headers: Referer=<iframe URL>, Origin=https://duanxianxia.com,
         X-Requested-With=XMLHttpRequest, Cookie=<上一步 Cookie>
→ {"stock_url": "https://qt.gtimg.cn/q=sz002790,...", "html": "..."}
```
`stock_url` 可直接请求腾讯批量行情，给池内个股补实时价；无 Cookie 通常也能过（只校验 Referer）。

### 9.4 板块强度 / 主力资金雷达（.cn）
```python
POST https://duanxianxia.cn/api/getLiveByStrong
form: platetype=strong|money, platelist=<88x/80x逗号分隔，可留空>
Referer: https://duanxianxia.cn/web/qxlive
→ {"checkplate": [...], "result": "success", "series": [...]}   # strong=强度, money=主力资金
```

### 9.5 涨停池快照（AES 加密 JSON）
```python
GET https://duanxianxia.com/vendor/stockdata/ztpool.json
# base64(AES-256-CBC-PKCS7)
# key=b"secretkey322yes!!aaaaaaaaaaaaaaa", iv=b"fixediv_16valued"
# 解密后: {"list": [[code,name,涨幅,封单额,开板次数,最近封板时间,涨停原因,板型,成交额,流通市值,腿型,连板数,首封时间], ...],
#          "count": {zt涨停/lb连板/zb炸板/dt跌停 数量, limit_up_count:{today:{num,history_num,rate封板率,open_num,lbnum},yesterday:{...}},
#                    limit_down_count:{...}}}   ← 情绪指标直接可用
```
（key/iv 来自公开仓库 easy-stock；站点若更换需社区重新确认。）

### 9.6 数据源发现
```python
GET https://duanxianxia.com/vendor/stockdata/datasource.json
→ {"istrade":0,"nocache":0,"data_url":"https://ds.duanxianxia.com","base_url":["https://duanxianxia.com"]}
```
备用域：`ds.duanxianxia.com`（数据）、`bm.duanxianxia.com`（开盘啦）、`x.duanxianxia.cn`。

### 9.7 开盘啦板块成分 / 子板块（bm 子域）
```python
POST https://bm.duanxianxia.com/data/getKaipanStock/web    form: plateCode=<80x/803x>
→ {"list": [[code, name, ..., 板数, ..., "5天3板"], ...]}
POST https://bm.duanxianxia.com/data/getKaipanSubPlate      form: plateCode=<80x/803x>
→ {"result": "<button class='subplate' plateCode='801839'>高速连接</button>..."}
```

### 9.8 实时板块推送（WebSocket）
```
wss://duanxianxia.com/wss1   # onmessage 为 JSON，适合盘中实时刷新
```

### 9.9 降级映射（token 功能 → 免费替代）

| token 功能 | 免费替代 |
|---|---|
| 涨停播报 | `ztlive.json`（实时）/ `ztpool.json`（解密快照） |
| 连板天梯 | `getHisZtPool(type=lianban)` |
| 涨停概念分组 | `getHisZtPool(type=plate)` |
| 板块轮动 | `getPlateRotatData` + `getLongByPlate` |
| 板块强度 | `getLiveByStrong(platetype=strong)` + `bm.getKaipanStock` |
| 主力资金流向 | `getLiveByStrong(platetype=money)` |
| 每日复盘 | `getFupanDate` + `getFupanByYidong` |
| 市场情绪面板 | `ztpool.json` 的 `count` 字段（涨停/跌停/炸板数、封板率、昨日对比），必要时叠加 fupan |
| 龙虎榜/个股异动解析/资讯播报/竞价类 | 无免费替代（需续费） |

### 9.10 参考实现

依赖：`pip install requests cryptography`

```python
import base64, json
import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.0 Safari/605.1.15")


def ajax_headers(referer, origin="https://duanxianxia.com"):
    return {"User-Agent": UA,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": origin, "Referer": referer,
            "X-Requested-With": "XMLHttpRequest"}


def get_plate_rotation(source="ths", days=20):
    """板块轮动 -> {"first": code, "html": "..."}（ths=涨幅%, kaipan=强度分）"""
    r = requests.post("https://duanxianxia.com/api/getPlateRotatData",
                      data={"from": source, "days": days, "dates": ""},
                      headers=ajax_headers("https://duanxianxia.com/web/platerotat/"),
                      timeout=15)
    return r.json()


def get_hist_zt_pool(date, pool_type="lianban"):
    """历史涨停池 -> {"stock_url": 腾讯行情, "html": "..."}（lianban=连板, plate=概念）"""
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    s.get("https://duanxianxia.com/web/zthis/iframe", timeout=15)  # 拿 Cookie
    r = s.post("https://duanxianxia.com/api/getHisZtPool",
               data={"date": date, "type": pool_type},
               headers={"Referer": "https://duanxianxia.com/web/zthis/iframe",
                        "Origin": "https://duanxianxia.com",
                        "X-Requested-With": "XMLHttpRequest"},
               timeout=20)
    return r.json()


def get_zt_pool_snapshot():
    """涨停池解密快照 -> {"list": [...], "count": 情绪统计}"""
    r = requests.get("https://duanxianxia.com/vendor/stockdata/ztpool.json",
                     headers={"User-Agent": UA}, timeout=15)
    ct = base64.b64decode(r.text.strip())
    dec = Cipher(algorithms.AES(b"secretkey322yes!!aaaaaaaaaaaaaaa"),
                 modes.CBC(b"fixediv_16valued")).decryptor()
    pt = dec.update(ct) + dec.finalize()
    pt = pt[:-pt[-1]]                                    # 去 PKCS7 padding
    return json.loads(pt.decode("utf-8"))
```

工程建议（社区实践）：429/5xx 指数退避重试（1s/2s/4s）；POST 结果可落盘缓存（板块类 TTL 1h）；
盘中请求 ≤1次/秒；返回的 `html` 是 innerHTML 片段，用 BeautifulSoup 解析，不要重新逆向。

## 十、情绪周期信号（盘后复盘必做）

每个交易日盘后复盘时，**必须**先跑一次情绪信号检测，并把结论写进复盘输出。规则如下（阈值可调，见代码常量 `PEAK/ICE/WARM`）：

| 信号 | 条件 | 动作 |
|---|---|---|
| ⚠️ 情绪顶点退潮 | 昨日情绪指标 **> 60**，且今日 涨停家数、封板率、赚钱效应（涨停表现或连板表现）**较昨日均下降** | **降仓** |
| 🧊 情绪冰点 | 今日情绪指标 **≤ 35** | **开始分批试探建仓** |
| 🔥 情绪回暖确认 | 今日情绪指标较昨日 **回升 ≥ 5**，且涨停家数回升，且（赚钱效应 或 封板率 回升） | **加仓** |

> 退潮期顶点信号可能连续触发（每天都是有效的降仓提醒）；冰点信号在指标明显回暖前会持续触发。
> 该信号仅为仓位节奏参考，不构成投资建议。

### 参考实现

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

## 十一、开盘竞价交易计划（9:25-9:30 必做）

9:25 竞价撮合完成后、9:30 开盘前有 5 分钟决策窗口，按本节流程输出当日交易计划。
（本节指标同时覆盖 **开盘竞价 9:15-9:25** 与 **尾盘竞价 14:57-15:00**。）

### 11.1 数据源

| 层级 | 工具 | 说明 |
|---|---|---|
| 市场级 | TDX 官方 MCP `tdx_screener("竞价高开")` / `("竞价抢筹")` | 全市场竞价名单；抢筹版带 `开盘抢筹(%)` 与自由流通股本（实测 2026-09-11：高开 586 家、抢筹榜 1520 条） |
| 市场级 | 短线侠 `mob/jjyd/{token}`（**需续费**） | 7 个 tab：涨停委买/昨日涨停/竞价爆量/竞价抢筹/竞价净额/昨炸板/昨断板/昨上榜；字段：竞价换手、竞涨、主力净买、竞额、竞价量比 |
| 个股级 | TDX 免费 MCP `stock_auction(market, code)` | 09:15-09:25 每 3 秒 `{time, price, matched, unmatched}` + 尾盘竞价；部分个股可能无数据，重试即可 |
| 个股级 | TDX 官方 MCP `tdx_quotes`（9:25 后） | 开盘价、竞价量、盘口、昨收 |

### 11.2 指标含义

- **竞价高开幅度** = 9:25 竞价价 / 昨收 − 1
- **matched（匹配量/手）**：已撮合量，衡量竞价人气
- **unmatched（未匹配量/手）**：**>0 = 买方剩余（抢筹）；<0 = 卖方剩余（抛压）**
- **尾段方向**：9:24 → 9:25 价格斜率（上翘=抢筹 / 下拐=跳水）
- **撤单观察**：9:15-9:20 可撤单（虚挂多），9:20-9:25 不可撤（意愿真实）
- **一字抢筹**：竞价即涨停 + 未匹配买量巨大

### 11.3 形态判定表

| 形态 | 条件 | 动作 |
|---|---|---|
| 一字抢筹 | 高开≈板幅 且 未匹配买量极大 | 情绪冰点只排不追；回暖可排板 |
| 强势高开 | 高开 +3~7% 且 匹配量放大 且 未匹配>0 | 半路/打板候选 |
| 弱转强 | 昨日炸板/断板 + 高开 +1~5% 且 未匹配>0 | 低吸/打板（重点） |
| 高开回落 | 9:15 涨停 → 9:25 大幅回落 且 未匹配转负 | 等分时承接，回封再打 |
| 核按钮 | 低开 ≤−5% 且 放量卖压 | 不接飞刀 |
| 缩量平开 | 平/低开 且 匹配量小 | 观望 |

### 11.4 计划模板（9:29 前出）

```
【今日交易计划 · YYYY-MM-DD】
1. 情绪定位：<降仓/建仓/加仓>（第十节信号）
2. 竞价温度：高开X家、抢筹榜方向；昨日连板梯队竞价强弱
3. 关注标的：
   | 代码 | 名称 | 昨日状态 | 竞价高开% | 匹配量 | 未匹配 | 形态 | 操作条件 | 仓位 |
4. 持仓处理：止盈/止损/持有
5. 仓位纪律：单票上限、总仓位、不接飞刀、不打缩量板
```

### 11.5 计算函数

```python
def auction_metrics(ticks, pre_close):
    """ticks: stock_auction 原始返回；取 09:15-09:25 段计算指标"""
    au = [t for t in ticks if "09:15" <= t["time"] <= "09:25"]
    if not au:
        return None
    last = au[-1]
    px = last["price"]
    late = next((t for t in reversed(au) if t["time"] <= "09:24:30"), au[0])
    return {
        "竞价价格": px,
        "高开幅度%": round((px / pre_close - 1) * 100, 2),
        "匹配量(手)": last["matched"],
        "未匹配量(手)": last["unmatched"],
        "未匹配方向": "买盘剩余(强)" if last["unmatched"] > 0 else "卖盘剩余(弱)",
        "尾段方向": "抢筹" if px > late["price"] else ("跳水" if px < late["price"] else "走平"),
    }
```

用法：9:25-9:30 对关注池（来自昨日涨停/连板梯队）逐票调 `stock_auction` → `auction_metrics`，
结合 11.3 判定表与第十节情绪周期信号，按 11.4 模板输出计划。

## 十二、注意事项

1. 域名：`duanxianxia.cn`、`duanxianxia.com` 及子域 `ds.`（数据）、`bm.`（开盘啦）、`x.duanxianxia.cn`，均支持 HTTPS
2. HTML 端点需配合 `BeautifulSoup` 或正则解析；JSON 端点：fupan 系列、getPlateRotatData、getLongByPlate、getHisZtPool、getLiveByStrong、bm 系列、ztpool（AES 加密）等
3. 页面数据均为**服务端渲染**，无需执行 JavaScript，requests 即可获取（实时推送 `wss://duanxianxia.com/wss1` 除外）
4. `{token}` 为用户身份标识，请勿泄露
5. 数据更新时效：涨停播报/情绪面板为**实时**，竞价异动仅在**竞价时段**(9:15-9:25)有数据
6. token 文件：`~/.claude/skills/duanxianxia/.token`（本地私有，勿提交）；token 失效时需向短线侠更新后覆盖该文件
7. `ztlive.json` 无需token但有频率限制，连续请求间隔建议 ≥ 10秒，否则返回 403
8. 盘中数据请求频率建议 ≤ 1次/秒，避免被限制
9. 已对接的现有脚本：`fetch_daily_zt.py`（使用 `fupan_date` + `fupan_yidong` API 获取历史涨停数据）
