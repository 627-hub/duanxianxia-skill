# 短线侠数据工具包

[短线侠](https://duanxianxia.cn) 非官方 Python 数据接口，覆盖涨停播报、竞价异动、板块强度、资金流向、龙虎榜、连板天梯、情绪指标、个股异动解析等 30+ 数据端点。

## 安装

```bash
pip install requests beautifulsoup4
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

1. HTML 端点需加 `User-Agent` 请求头，否则返回 403
2. `ztlive.json` 有频率限制，连续请求间隔 ≥ 10 秒
3. 竞价数据仅在 9:15-9:25 时段有效
4. 盘中请求频率建议 ≤ 1 次/秒
5. token 请勿泄露到公开仓库

## 许可证

MIT
