# Virtual Protocol AI Agent 数据爬虫

自动化爬虫系统，用于采集 [Virtuals Protocol ACP（Agent Commerce Protocol）](https://app.virtuals.io/acp/scan) 平台上所有 AI Agent 的完整数据，包括性能指标、服务内容、钱包地址等，最终输出为格式化的 Excel 文件。

## 功能特点

- **纯 API 爬取** — 无需浏览器自动化；通过逆向工程发现 API 端点，速度快、稳定性高
- **数据全面** — 每个 Agent 采集 35 个字段，涵盖 5 大类别
- **Excel 格式化输出** — 两级合并表头、Agent 超链接、自适应列宽、冻结窗格、中文本地化内容
- **异步并发** — 可配置并发数，内置限速和重试机制
- **定时运行** — 内置调度器，支持每日/每小时自动采集

## 采集的数据

| 分类 | 字段 |
|---|---|
| **核心信息 (Core Info)** | 排名、Agent 链接（可点击超链接）、名称、分类、介绍 |
| **关键指标 (Key Metrics)** | 交易量（总 AGDP）、总 AGDP、总收入、成功率、评分 |
| **活跃度 (Activity)** | 交易笔数、成功任务数、独立买家数、在线状态、最后活跃时间 |
| **服务内容 (What I Offer)** | 服务名称、服务描述、价格、SLA 时限、服务要求 |
| **身份与链接 (Identity & Links)** | 钱包地址、合约地址、Token 地址、Owner 地址、Twitter、Symbol、角色、集群、是否毕业、余额、支持链、Virtual Agent ID、创建时间、头像 URL |

## 使用的 API 端点

所有数据来源于 `acpx.virtuals.io` 的公开 API（通过 Playwright 网络拦截发现）：

| 端点 | 说明 |
|---|---|
| `GET /api/agents` | Agent 列表，包含服务内容和基础信息 |
| `GET /api/metrics/agents` | 排行榜数据，包含交易量、收入、成功率 |
| `GET /api/metrics/four-metrics` | 平台级 AGDP 时间序列数据 |
| `GET /api/agents/{id}/details` | 单个 Agent 详情（介绍、服务、钱包等） |
| `GET /api/metrics/agent/{id}` | 单个 Agent 指标（交易量、收入、7 天数据） |

## 快速开始

### 环境要求

- Python 3.8+
- pip

### 安装

```bash
git clone https://github.com/Oceanjackson1/Virtual-Protocol-AI-Agent-Data-Scraping.git
cd Virtual-Protocol-AI-Agent-Data-Scraping
pip install -r requirements.txt
```

### 单次运行

```bash
python -m src.main
```

或使用启动脚本：

```bash
chmod +x run_scraper.sh
./run_scraper.sh
```

输出的 Excel 文件将保存至 `./output/acp_agents_YYYYMMDD_HHMMSS.xlsx`。

### 定时运行模式

1. 编辑 `config.yaml`：

```yaml
schedule:
  enabled: true
  interval_hours: 24
  run_at: "08:00"
```

2. 启动调度器：

```bash
./run_scraper.sh schedule
```

也可以使用 cron 定时任务：

```bash
# 每天早上 8 点运行
0 8 * * * cd /path/to/Virtual-Protocol-AI-Agent-Data-Scraping && python -m src.main
```

## 配置说明

所有配置项在 `config.yaml` 中：

```yaml
scraper:
  concurrency: 3          # 并发请求数
  request_delay_sec: 1.5  # 请求间隔（秒）
  max_retries: 3          # 失败重试次数

output:
  directory: "./output"         # 输出目录
  filename_prefix: "acp_agents" # Excel 文件名前缀

schedule:
  enabled: false          # 是否启用定时运行
  interval_hours: 24      # 运行间隔（小时）
  run_at: "08:00"         # 每日运行时间（仅 interval_hours=24 时生效）
```

## 项目结构

```
├── config.yaml              # 爬虫配置文件
├── requirements.txt         # Python 依赖
├── run_scraper.sh           # 启动脚本
├── src/
│   ├── __init__.py
│   ├── main.py              # 主入口
│   ├── scraper.py           # 核心爬虫（异步 API 调用）
│   ├── models.py            # 数据模型（AgentData, Offering, GlobalMetrics）
│   ├── excel_exporter.py    # Excel 导出（两级表头、超链接）
│   ├── scheduler.py         # 定时任务
│   └── api_discovery.py     # API 端点发现工具（Playwright）
└── output/                  # Excel 输出目录
```

## Excel 输出格式

生成的 Excel 文件采用单 Sheet 布局：

- **第 1 行**：一级分类表头（合并单元格，深蓝底白字）
- **第 2 行**：二级字段表头（浅蓝底深色字）
- **第 3 行起**：Agent 数据，每行一个 Agent，按交易量降序排列
- **Agent Link 列**：可点击的超链接，直接跳转到对应 Agent 的详情页
- **冻结窗格**：前两行表头固定，滚动时始终可见
- **自动筛选**：所有列启用筛选器
- **汇总信息**：表格底部显示爬取时间、Agent 总数、平台总 AGDP

## 技术栈

| 库 | 用途 |
|---|---|
| **aiohttp** | 异步 HTTP 客户端，用于 API 调用 |
| **openpyxl** | Excel 文件生成与样式设置 |
| **PyYAML** | 配置文件解析 |
| **schedule** | 定时任务调度 |
| **Playwright** | API 端点发现（可选，仅 `api_discovery.py` 使用） |

## 许可证

MIT
