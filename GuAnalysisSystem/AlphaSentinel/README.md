# AlphaSentinel 期货智能分析系统

## 项目概述

AlphaSentinel是一款专业的期货市场智能分析系统，结合了量化交易策略、技术分析和人工智能辅助决策功能，为期货投资者提供全面的市场监控、数据分析和交易决策支持。系统采用模块化设计，具有高度的扩展性和灵活性，可满足不同投资者的个性化需求。

## 主要功能模块及特性说明

### 1. 市场监控与数据获取
- **实时数据采集**：通过akshare等数据源实时获取期货市场行情数据
- **多交易所支持**：覆盖上海期货交易所(SHFE)、大连商品交易所(DCE)、郑州商品交易所(CZCE)、中国金融期货交易所(CFFEX)等国内主要期货交易所
- **历史数据存储**：自动存储历史行情数据，支持回测分析

### 2. 技术分析模块
- **技术指标计算**：支持RSI、MACD、KDJ、BOLL等多种常用技术指标
- **图表可视化**：通过Plotly和Matplotlib生成专业的K线图和指标走势图
- **多周期分析**：支持分钟、小时、日线等多种时间周期的技术分析

### 3. AI智能分析
- **模型集成**：支持Google Gemini、SiliconFlow等多种AI模型
- **市场趋势分析**：AI辅助判断市场趋势和关键点位
- **交易信号生成**：基于AI分析生成潜在的交易信号
- **模型管理**：提供模型的添加、编辑、删除和参数调整功能

### 4. 策略管理系统
- **策略开发框架**：提供量化交易策略的开发和测试框架
- **多策略支持**：支持同时运行多个不同的交易策略
- **策略回测**：基于历史数据进行策略回测和绩效评估

### 5. 预警与通知
- **自定义预警条件**：支持价格、成交量、持仓量等多种条件的预警设置
- **多渠道通知**：支持邮件等通知方式
- **实时监控**：24小时监控市场动态，及时触发预警

### 6. Web Dashboard
- **直观的数据展示**：通过Streamlit构建的Web界面，提供直观的数据可视化
- **交互式操作**：支持实时查询、参数调整和策略管理
- **响应式设计**：适配不同设备的屏幕尺寸

## 技术栈介绍

| 类别 | 技术/框架 | 版本要求 | 用途 |
|------|----------|----------|------|
| 核心语言 | Python | ≥3.9 | 系统开发 |
| 数据获取 | akshare | ≥1.10.30 | 期货数据采集 |
| AI模型 | google-generativeai | ≥0.4.0 | Gemini模型集成 |
| 数据处理 | pandas | ≥1.5.0 | 数据处理与分析 |
| 数据计算 | numpy | ≥1.24.0 | 数值计算 |
| 可视化 | matplotlib | ≥3.7.0 | 图表生成 |
| 可视化 | plotly | ≥5.15.0 | 交互式图表 |
| Web框架 | streamlit | ≥1.25.0 | Web Dashboard构建 |
| 任务调度 | apscheduler | ≥3.10.0 | 定时任务管理 |
| 配置管理 | pyyaml | ≥6.0 | 配置文件处理 |
| 网络请求 | requests | ≥2.31.0 | API请求 |
| 网页解析 | beautifulsoup4 | ≥4.12.0 | 网页数据提取 |
| 数据库 | SQLAlchemy | ≥2.0.0 | 数据存储（可选） |

## 环境要求

- **操作系统**：Windows 10/11、Linux、macOS
- **Python版本**：Python 3.9或更高版本
- **内存**：建议8GB以上
- **磁盘空间**：建议10GB以上（用于存储历史数据）
- **网络连接**：稳定的网络连接（用于数据获取和AI模型调用）

## 部署步骤

### 1. 环境准备

#### 1.1 安装Python

请从[Python官网](https://www.python.org/downloads/)下载并安装Python 3.9或更高版本。安装时请勾选"Add Python to PATH"选项。

#### 1.2 安装依赖管理工具

建议使用pip或conda进行依赖管理。如果使用conda，可以创建一个新的虚拟环境：

```bash
conda create -n alphasentinel python=3.9
conda activate alphasentinel
```

### 2. 项目下载

克隆或下载项目代码到本地：

```bash
git clone <repository-url>
cd AlphaSentinel
```

### 3. 安装依赖

使用pip安装项目所需的依赖包：

```bash
pip install -r requirements.txt
```

### 4. 配置文件设置

项目的主要配置文件位于`config`目录下：

#### 4.1 模型配置 (models.json)

配置AI模型的连接信息：

```json
[
  {
    "name": "Gemini",
    "type": "google_gemini",
    "api_key": "your-api-key",
    "model_id": "gemini-pro",
    "enabled": true
  },
  {
    "name": "SiliconFlow",
    "type": "siliconflow",
    "api_key": "your-api-key",
    "model_id": "qwen2-72b-chat",
    "enabled": true
  }
]
```

#### 4.2 提示词配置 (prompts.yaml)

配置AI模型的提示词模板：

```yaml
trend_analysis:
  template: "请分析以下期货品种的趋势：{symbol}\n\n{data}\n\n请提供简洁的趋势分析结果。"
  language: "zh-CN"
```

#### 4.3 系统设置 (settings.yaml)

配置系统的基本参数：

```yaml
# 数据获取设置
data:
  update_interval: 60  # 数据更新间隔（秒）
  max_history_days: 365  # 最大历史数据天数

# 策略设置
strategy:
  default_strategy: "ma_crossover"  # 默认策略
  risk_level: "medium"  # 风险等级：low/medium/high

# 预警设置
alert:
  enabled: true
  email: "your-email@example.com"
```

#### 4.4 品种池配置 (symbols_pool.txt)

配置关注的期货品种列表：

```
rb2505
hc2505
cu2505
al2505
a2505
m2505
```

### 5. 创建必要的目录

系统需要以下目录来存储数据和日志：

```bash
mkdir -p logs db data/history
```

## 运行方法

### 开发环境

#### 1. 运行主程序（后台监控）

```bash
python main.py
```

#### 2. 运行Web Dashboard

```bash
streamlit run dashboard_v6.py
```

启动后，在浏览器中访问 http://localhost:8501 即可使用Web界面。

### 生产环境

#### 1. 使用systemd（Linux）

创建systemd服务文件 `/etc/systemd/system/alphasentinel.service`：

```ini
[Unit]
Description=AlphaSentinel Futures Analysis System
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/AlphaSentinel
ExecStart=/path/to/python main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

启用并启动服务：

```bash
sudo systemctl enable alphasentinel
sudo systemctl start alphasentinel
```

#### 2. 使用Docker（推荐）

创建Dockerfile：

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

构建并运行容器：

```bash
docker build -t alphasentinel .
docker run -d --name alphasentinel alphasentinel
```

对于Web Dashboard，可以使用以下命令：

```bash
docker run -d -p 8501:8501 --name alphasentinel-dashboard alphasentinel streamlit run dashboard_v6.py
```

## 系统结构

```
AlphaSentinel/
├── analysis/          # 分析模块
│   ├── chart_plotter.py      # 图表绘制
│   ├── gemini_client.py      # Gemini AI客户端
│   ├── model_manager.py      # AI模型管理
│   ├── siliconflow_client.py # SiliconFlow AI客户端
│   └── technical_calc.py     # 技术指标计算
├── config/            # 配置文件
│   ├── models.json           # AI模型配置
│   ├── prompts.yaml          # 提示词模板
│   ├── settings.yaml         # 系统设置
│   └── symbols_pool.txt      # 期货品种池
├── data/              # 数据模块
│   ├── data_loader.py        # 数据加载器
│   ├── data_utils.py         # 数据工具函数
│   └── news_scraper.py       # 新闻爬取
├── engine/            # 核心引擎
│   ├── notifier.py           # 通知系统
│   ├── scheduler.py          # 任务调度器
│   └── strategy_manager.py   # 策略管理器
├── ui/                # 用户界面
│   └── model_management.py   # 模型管理界面
├── .streamlit/        # Streamlit配置
│   └── config.toml           # Streamlit配置文件
├── logs/              # 日志目录
├── db/                # 数据库目录
├── main.py            # 主程序入口
├── dashboard_v6.py    # Web Dashboard入口
├── requirements.txt   # 依赖列表
└── README.md          # 项目文档
```

## 常见问题解决

### 1. 数据获取失败

**问题**：无法获取期货行情数据

**解决方案**：
- 检查网络连接是否正常
- 确认akshare版本是否最新：`pip install --upgrade akshare`
- 检查期货品种代码是否正确
- 查看logs目录下的日志文件，分析具体错误信息

### 2. AI模型连接失败

**问题**：无法连接到AI模型服务

**解决方案**：
- 检查API密钥是否正确配置
- 确认网络可以访问模型服务
- 检查模型ID是否存在且可用
- 查看logs目录下的日志文件，分析具体错误信息

### 3. Web界面无法访问

**问题**：启动Streamlit后无法访问Web界面

**解决方案**：
- 检查是否有防火墙或端口占用问题
- 确认Streamlit是否正常启动：查看控制台输出
- 尝试使用不同的浏览器或清除浏览器缓存

### 4. 策略运行异常

**问题**：策略运行时出现错误

**解决方案**：
- 检查策略代码是否有语法错误
- 确认策略依赖的技术指标是否正确计算
- 查看logs目录下的策略运行日志
- 使用回测功能测试策略的正确性

## 维护与更新

### 定期更新

1. **更新数据源**：定期更新akshare库以获取最新的数据接口
2. **更新AI模型**：关注AI模型的更新，及时调整模型参数
3. **优化策略**：根据市场变化，定期优化交易策略

### 数据备份

建议定期备份以下数据：
- 历史行情数据（data/history目录）
- 策略配置和回测结果
- 系统日志（logs目录）

## 许可证

[MIT License](LICENSE)

## 联系方式

如有问题或建议，请通过以下方式联系：

- 项目维护者：[Your Name]
- 邮箱：[your-email@example.com]
- GitHub：[github.com/your-username/AlphaSentinel]

## 贡献指南

欢迎对项目进行贡献！贡献者请遵循以下步骤：

1. Fork项目仓库
2. 创建特性分支：`git checkout -b feature/new-feature`
3. 提交修改：`git commit -am 'Add new feature'`
4. 推送到分支：`git push origin feature/new-feature`
5. 提交Pull Request

## 版本历史

- v1.0.0 (2026-01-18)：初始版本，包含核心功能模块
- v1.1.0 (2026-02-15)：增加AI模型集成和Web Dashboard
- v1.2.0 (2026-03-20)：优化策略管理系统和预警功能

---

**AlphaSentinel** - 让期货投资更智能、更高效！