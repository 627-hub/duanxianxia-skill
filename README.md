# 短线侠数据工具包

[短线侠](https://duanxianxia.cn) 非官方 Python 数据接口与 opencode Skill，覆盖涨停播报、竞价异动、板块强度、资金流向、龙虎榜、连板天梯、情绪指标、个股异动解析等 30+ 数据端点；内置**免 token 免费降级通道**（账号过期/未续费时可用）、**盘后情绪信号**（情绪顶点→降仓提醒，冰点→建仓提示，回暖→加仓提示）与**开盘竞价交易计划**（9:25-9:30 五分钟出计划）。

> 🔗 **邀请链接（注册/续费入口）**：https://duanxianxia.com/276946

## 安装

```bash
pip install requests beautifulsoup4 cryptography   # cryptography 用于解密涨停池快照
```

## 快速开始

```python
from duanxianxia import DuanXianXia

dx = DuanXianXia(token="<YOUR_TOKEN>")

# 涨停播报 (JSON API, 无需token)
zt_list = dx.zt_live_json()
for s in zt_list[:5]:
    print(f"{s['code']} {s['name']} | {s['zt']} | {s['ztyy']}")

# 市场情绪概览
sentiment = dx.qixi_overview()
print(sentiment)

# 每日复盘
fupan = dx.fupan_by_yidong("20260707")
print(fupan["indicators"])
```

## opencode Skill 使用

将此目录作为 opencode skill 加载，对话中直接询问：

- "今天涨停的股票有哪些？"
- "市场情绪怎么样？"
- "查看一下 600288 的异动原因"
- "帮我分析今日板块强度排名"
- "获取 20260707 的复盘数据"
- "盘后复盘：现在该降仓还是建仓？"
- "今日竞价怎么样？帮我出交易计划"

## 数据端点

| 类别 | 端点 | 说明 |
|------|------|------|
| **涨停播报** | `/vendor/livedata/ztlive.json` | JSON API，无需 token |
| **涨停播报** | `/web/ztlive/{token}/light` | HTML，需 token |
| **股票池** | `/web/pool/{token}` | 多维度聚合 |
| **连板天梯** | `/web/lianban/{token}` | 各连板层级分布 |
| **竞价异动** | `/mob/jjyd/{token}` | 盘前竞价信号 |
| **板块强度** | `/stock/strong/{token}/light` | 板块排名+个股 |
| **沪深量能** | `/web/amount/{token}` | 大盘活跃度 |
| **资金流向** | `/stock/fund/{token}` | 主力+北向资金 |
| **市场情绪** | `/web/qxlive/{token}` | 综合情绪仪表盘 |
| **个股异动** | `/stock/yidong/{token}/{code}` | 历史异动原因 |
| **个股信息** | `/stock/showbasic/{token}/{code}` | 基本面+概念 |
| **龙虎榜** | `/web/longhu/{token}` | 席位数据 |
| **热点聚焦** | `/web/hotnews/{token}/tdx` | 综合资讯 |
| **复盘日期** | `POST /api/getFupanDate` | JSON，无需 token |
| **复盘异动** | `POST /api/getFupanByYidong` | JSON，无需 token |

## 免 Token 免费通道（账号过期时作为降级）

以下端点**无需 token**，2026-09 实测全部可用。完整说明与实现见 `SKILL.md` 第九章。

| 类别 | 端点 | 返回 |
|------|------|------|
| **板块轮动** | `POST .com/api/getPlateRotatData` | `{first, html}`（ths=涨幅% / kaipan=强度分） |
| **板块龙头** | `POST .com/api/getLongByPlate` | `{html}`（龙一~龙N） |
| **历史涨停池** | `POST .com/api/getHisZtPool` | `{stock_url(腾讯行情), html}`（lianban/plate） |
| **板块强度/资金** | `POST .cn/api/getLiveByStrong` | `{series}`（strong/money） |
| **涨停池快照** | `GET .com/vendor/stockdata/ztpool.json` | AES 加密：`{list, count 情绪统计}` |
| **开盘啦成分股** | `POST bm.duanxianxia.com/data/getKaipanStock/web` | `{list}`（plateCode=80x/803x） |
| **开盘啦子板块** | `POST bm.duanxianxia.com/data/getKaipanSubPlate` | `{result}` |
| **实时推送** | `wss://duanxianxia.com/wss1` | WebSocket JSON |

要求：完整浏览器 UA；AJAX 接口带 `Referer`/`Origin`/`X-Requested-With`。
涨停池快照解密参数（公开常量）：`AES-256-CBC`，key=`secretkey322yes!!aaaaaaaaaaaaaaa`，iv=`fixediv_16valued`。

```python
import base64, json, requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# 涨停池快照（AES 解密，count 含涨停/连板/炸板/跌停数与封板率）
raw = requests.get("https://duanxianxia.com/vendor/stockdata/ztpool.json",
                   headers={"User-Agent": "Mozilla/5.0"}, timeout=15).text
ct = base64.b64decode(raw.strip())
dec = Cipher(algorithms.AES(b"secretkey322yes!!aaaaaaaaaaaaaaa"),
             modes.CBC(b"fixediv_16valued")).decryptor()
pt = dec.update(ct) + dec.finalize()
pt = pt[:-pt[-1]]  # 去 PKCS7 padding
data = json.loads(pt)
print(data["count"]["limit_up_count"]["today"])  # 涨停数/封板率/连板数
```

## Python 示例

### 涨停播报 (JSON)

```python
import requests

resp = requests.get(
    "https://duanxianxia.cn/vendor/livedata/ztlive.json",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=15
)
data = resp.json()
for item in data["list"][:10]:
    print(f"{item['code']} {item['name']:6s} | {item['zt']:8s} | {item['ztyy']}")
```

### 市场情绪

```python
import requests
from bs4 import BeautifulSoup

TOKEN = "<YOUR_TOKEN>"
resp = requests.get(
    f"https://duanxianxia.cn/web/qxlive/{TOKEN}",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=15
)
resp.encoding = "utf-8"
soup = BeautifulSoup(resp.text, "html.parser")
text = soup.get_text(separator="\n", strip=True)
print(text)
```

### 每日复盘

```python
import requests

resp = requests.post(
    "https://duanxianxia.com/api/getFupanByYidong",
    data={"date": "20260707", "type": "plate"},
    timeout=15
)
data = resp.json()
print(data["htmlcopy"][:500])  # 情绪指标+涨停分组
```

### 个股异动解析

```python
import requests
from bs4 import BeautifulSoup

TOKEN = "<YOUR_TOKEN>"
resp = requests.get(
    f"https://duanxianxia.cn/stock/yidong/{TOKEN}/600288",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=15
)
resp.encoding = "utf-8"
soup = BeautifulSoup(resp.text, "html.parser")
print(soup.get_text(separator="\n", strip=True))
```

### 板块强度

```python
import requests
from bs4 import BeautifulSoup

TOKEN = "<YOUR_TOKEN>"
resp = requests.get(
    f"https://duanxianxia.cn/stock/strong/{TOKEN}/light",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=15
)
resp.encoding = "utf-8"
soup = BeautifulSoup(resp.text, "html.parser")
text = soup.get_text(separator="\n", strip=True)
lines = [l.strip() for l in text.split("\n") if l.strip()]
for line in lines[:20]:
    print(line)
```

## 注意事项

1. 域名：`duanxianxia.cn`、`duanxianxia.com` 及子域 `ds.`（数据）、`bm.`（开盘啦）、`x.duanxianxia.cn`；HTML 端点需带完整浏览器 UA（短 UA 可能 403）
2. `ztlive.json` 有频率限制，连续请求间隔 ≥ 10 秒；盘中请求频率建议 ≤ 1 次/秒
3. 竞价数据仅在 9:15-9:25 时段有效
4. 板块代码不可跨源：同花顺 `88x`=涨幅%，开盘啦 `80x/803x`=强度分，platecode 不可混传
5. token 请勿泄露到公开仓库（建议用本地文件或环境变量保存）

## 许可证

MIT
