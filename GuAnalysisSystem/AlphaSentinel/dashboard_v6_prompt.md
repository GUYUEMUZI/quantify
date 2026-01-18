# Role
你是一位资深的Python量化交易系统开发专家，精通GUI开发（如Streamlit/PyQt/Dash）以及数据可视化（Matplotlib/Plotly/Pyecharts）。

# Task
请针对我提供的现有代码进行重构和功能升级。目标是修复数据显示bug，优化UI布局，并增加技术指标交互功能。

# Context & Constraints
当前代码存在K线和期权数据无法显示的问题，且布局需要调整。请严格按照以下步骤修改代码：

## 1. Bug修复 (Bug Fixes)
- **修复K线显示**：检查数据获取和绘图逻辑，确保期货K线图能正常渲染并显示最新数据。
- **修复期权数据**：检查期权数据源接口及数据清洗逻辑，解决数据为空或无法加载的问题。

## 2. UI布局重构 (UI Layout Redesign)
请将界面重构为**横向三栏布局 (Three-Column Layout)**，每一栏独立显示以下内容：
- **第一栏 (Left Column)**：
    - **期货K线主图**：显示价格走势。
    - **技术指标控制区**：包含指标选择和参数设置。
- **第二栏 (Middle Column)**：
    - **持仓量数据**：显示当前的持仓量/成交量分析图表或数据表。
- **第三栏 (Right Column)**：
    - **期权数据看板**：必须使用**独立的容器/框**单独显示期权T型报价或相关列表，确保与期货数据视觉分离。

## 3. 功能增强 (Feature Enhancements)
- **指标系统升级**：
    - 在第一栏增加一个**下拉选择框 (Dropdown)**，包含常用指标：`BOLL`, `RSI`, `KDJ`, `CCI`。
    - 当用户选择某个指标时，自动在K线图下方或叠加显示该指标线。
    - 预留/实现“上传指标”或“自定义指标”的接口逻辑（允许用户输入简单的计算逻辑或加载外部文件）。
- **数据刷新频率**：
    - 将数据自动刷新/轮询机制调整为 **每30秒一次**。确保定时器逻辑不会导致界面卡顿。

## 4. 代码清理 (Code Cleanup)
- **删除冗余代码**：彻底删除之前版本中不再使用的函数、变量和注释出的旧代码，保持代码整洁。
- **模块化**：如果代码过长，请将数据获取、计算指标、UI渲染拆分为清晰的函数。

# Output Requirements
1. 请直接提供**完整、可运行的**修改后代码。
2. 在代码关键部分（特别是指标计算和布局部分）加上中文注释。
3. 如果涉及到新的第三方库（如talib），请说明需要安装的依赖。

# Current Code
```python
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import pytz
import json
import os
import akshare as ak
from streamlit_autorefresh import st_autorefresh

# 设置页面配置
st.set_page_config(
    page_title="AlphaSentinel V6 - 期货智能分析系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS 样式 - 深色/赛博朋克风格
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .stMetric {
        background-color: #161821;
        border-radius: 8px;
        padding: 16px;
        border: 1px solid #2D3748;
    }
    .stMetric .metric-label {
        color: #A0AEC0;
    }
    .stMetric .metric-value {
        color: #FAFAFA;
    }
    .stButton > button {
        background-color: #1E40AF;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 8px 16px;
        transition: background-color 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #3B82F6;
    }
    .long-highlight {
        background-color: rgba(16, 185, 129, 0.2) !important;
        font-weight: bold;
    }
    .short-highlight {
        background-color: rgba(239, 68, 68, 0.2) !important;
        font-weight: bold;
    }
    .stTabs [data-baseweb="tab-list"] {
        background-color: #161821;
        border-radius: 8px 8px 0 0;
    }
    .stTabs [data-baseweb="tab"] {
        color: #A0AEC0;
        padding: 10px 20px;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #1E40AF;
        color: white;
        border-radius: 4px;
    }
    .stTextArea textarea {
        background-color: #1A202C;
        color: #FAFAFA;
        border: 1px solid #2D3748;
    }
    .stForm {
        background-color: #161821;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #2D3748;
    }
    .stProgress > div > div {
        background-color: #10B981;
    }
</style>
""", unsafe_allow_html=True)

# 配置文件路径
CONFIG_FILE = 'config.json'

# 加载配置
@st.cache_data
def load_config():
    """从config.json文件加载配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 更新session_state
                for key, value in config.items():
                    if key != "BASE_PRICES":  # 不再加载BASE_PRICES
                        st.session_state[key] = value
            return True
        except Exception as e:
            st.error(f"加载配置文件失败: {str(e)}")
            return False
    return False

# 保存配置
def save_config():
    """将session_state保存到config.json文件"""
    config = {
        "system_prompt": st.session_state.system_prompt,
        "strategy_context": st.session_state.strategy_context,
        "gemini_api_key": st.session_state.gemini_api_key,
        "main_contracts": st.session_state.main_contracts,
        "notification_email": st.session_state.notification_email
        # 不再保存BASE_PRICES
    }
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"保存配置文件失败: {str(e)}")
        return False

# 初始化会话状态
def init_session_state():
    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = "你是一位拥有20年期货交易经验的资深交易员，擅长技术分析和量化策略制定。请基于提供的市场数据和技术指标，给出专业、准确的交易建议。"
    
    if "strategy_context" not in st.session_state:
        st.session_state.strategy_context = "重点关注15分钟K线的底背离形态，结合成交量变化判断趋势反转信号。当RSI指标低于30且出现MACD金叉时，考虑做多；当RSI高于70且出现MACD死叉时，考虑做空。"
    
    if "gemini_api_key" not in st.session_state:
        st.session_state.gemini_api_key = ""
    
    if "main_contracts" not in st.session_state:
        st.session_state.main_contracts = "RB2605, AG2602, CU2603, M2605, RU2605, AL2605, ZN2605, SN2605"
    
    if "notification_email" not in st.session_state:
        st.session_state.notification_email = ""
    
    # 固化邮件配置
    if "smtp_server" not in st.session_state:
        st.session_state.smtp_server = "smtp.163.com"
    if "smtp_port" not in st.session_state:
        st.session_state.smtp_port = 465
    if "email_user" not in st.session_state:
        st.session_state.email_user = "guyueqihuotixing@163.com"
    if "email_password" not in st.session_state:
        st.session_state.email_password = "LBH30-hui"

# 获取真实市场数据
def fetch_market_data(symbol, period):
    """使用AkShare获取真实期货分钟级数据"""
    try:
        # 智能合约代码清洗：转换为小写并去除交易所前缀
        symbol = symbol.lower().split('.')[-1]
        
        # 使用AkShare获取期货分钟数据
        df = ak.futures_zh_minute_sina(symbol=symbol, period=period)
        
        # 空数据防御
        if df is None or df.empty:
            st.error("未获取到数据，请检查合约代码是否有效（例如是否已过期）")
            return pd.DataFrame(columns=['Date', 'Date_Str', 'Open', 'High', 'Low', 'Close', 'Volume', 'OpenInterest'])
        
        # 暴力清洗：将所有列名转为小写
        df.columns = [col.lower() for col in df.columns]
        
        # 模糊匹配重命名列名
        new_columns = {}
        for col in df.columns:
            if 'time' in col or 'date' in col:
                new_columns[col] = 'Time'
            elif any(key in col for key in ['open', 'kai', '开盘']):
                new_columns[col] = 'Open'
            elif any(key in col for key in ['high', 'gao', '最高']):
                new_columns[col] = 'High'
            elif any(key in col for key in ['low', 'di', '最低']):
                new_columns[col] = 'Low'
            elif any(key in col for key in ['close', 'shou', '收盘']):
                new_columns[col] = 'Close'
            elif any(key in col for key in ['volume', 'vol', '成交量']):
                new_columns[col] = 'Volume'
            elif any(key in col for key in ['hold', '持仓', '持仓量']):
                new_columns[col] = 'OpenInterest'
        
        df = df.rename(columns=new_columns)
        
        # 确保有Time列，如果没有则使用索引
        if 'Time' not in df.columns:
            # 尝试使用索引作为时间
            if df.index.name in ['datetime', 'day', 'date', '日期', '日期时间']:
                df['Time'] = df.index
            else:
                st.warning("未找到时间列，使用当前时间生成默认数据")
                # 生成默认的时间序列
                df['Time'] = pd.date_range(end=datetime.now(), periods=len(df), freq=f'{period}T')
        
        # 将时间列转换为datetime类型
        df['Date'] = pd.to_datetime(df['Time'], errors='coerce')
        
        # 确保所有必要的列都存在
        for col in ['Open', 'High', 'Low', 'Close', 'Volume', 'OpenInterest']:
            if col not in df.columns:
                df[col] = 0
        
        # 强制类型转换
        df['Open'] = pd.to_numeric(df['Open'], errors='coerce').astype(float)
        df['High'] = pd.to_numeric(df['High'], errors='coerce').astype(float)
        df['Low'] = pd.to_numeric(df['Low'], errors='coerce').astype(float)
        df['Close'] = pd.to_numeric(df['Close'], errors='coerce').astype(float)
        df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce').astype(float)
        df['OpenInterest'] = pd.to_numeric(df['OpenInterest'], errors='coerce').astype(float)
        
        # 空值填充
        df = df.fillna(method='ffill').fillna(method='bfill')
        
        # 为绘图准备字符串格式的时间列
        df['Date_Str'] = df['Date'].dt.strftime('%Y-%m-%d %H:%M')

        # 选择需要的列，包含字符串格式的时间列
        df = df[['Date', 'Date_Str', 'Open', 'High', 'Low', 'Close', 'Volume', 'OpenInterest']]

        return df
    except Exception as e:
        st.error(f"获取数据失败: {str(e)}")
        return pd.DataFrame(columns=['Date', 'Date_Str', 'Open', 'High', 'Low', 'Close', 'Volume', 'OpenInterest'])

# 计算技术指标
def calculate_indicators(df):
    """计算各种技术指标"""
    # 计算BOLL（布林带）
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['STD20'] = df['Close'].rolling(window=20).std()
    df['UB'] = df['MA20'] + 2 * df['STD20']
    df['LB'] = df['MA20'] - 2 * df['STD20']
    
    # 计算RSI（相对强弱指数）
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 计算KDJ指标
    low9 = df['Low'].rolling(window=9).min()
    high9 = df['High'].rolling(window=9).max()
    df['RSV'] = (df['Close'] - low9) / (high9 - low9) * 100
    df['K'] = df['RSV'].ewm(alpha=1/3, adjust=False).mean()
    df['D'] = df['K'].ewm(alpha=1/3, adjust=False).mean()
    df['J'] = 3 * df['K'] - 2 * df['D']
    
    # 计算CCI（顺势指标）
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    ma_tp = tp.rolling(window=14).mean()
    mad = tp.rolling(window=14).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
    df['CCI'] = (tp - ma_tp) / (0.015 * mad)
    
    return df

# 获取期权情绪指标
def get_option_pcr(symbol):
    """获取期权PCR指标或持仓量变化率"""
    try:
        # 尝试使用AkShare获取该品种当月的期权数据
        symbol = symbol.lower().split('.')[-1]
        option_df = ak.option_zh_spot_price(symbol=symbol)
        
        if option_df is None or option_df.empty:
            raise Exception("期权数据为空")
        
        # 计算PCR (Put/Call Ratio)
        put_volume = option_df[option_df['类型'] == '认沽']['成交量'].sum()
        call_volume = option_df[option_df['类型'] == '认购']['成交量'].sum()
        
        if call_volume > 0:
            pcr = put_volume / call_volume
        else:
            pcr = 1.0
        
        return {"pcr": pcr, "type": "options"}
    except Exception as e:
        # 如果期权数据获取失败，使用持仓量变化率代替
        try:
            df = ak.futures_zh_minute_sina(symbol=symbol.lower(), period="5")
            if df is not None and not df.empty:
                # 处理列名
                df.columns = [col.lower() for col in df.columns]
                if any(col in df.columns for col in ['hold', '持仓', '持仓量']):
                    hold_col = next(col for col in df.columns if 'hold' in col or '持仓' in col)
                    oi_change_rate = df[hold_col].pct_change().mean() * 100
                    return {"pcr": oi_change_rate, "type": "open_interest"}
        except:
            pass
        
        return {"pcr": 1.0, "type": "default"}

# 分析市场函数（动态生成AI分析结果）
def analyze_market(symbol, candlestick_data, change_percent):
    """基于最新K线数据和涨跌幅生成动态分析结果"""
    if candlestick_data.empty:
        return {
            "symbol": symbol,
            "trend": "数据获取失败",
            "analysis": "无法获取有效的市场数据",
            "rsi_analysis": "RSI: 无数据",
            "rsi_suggestion": "无法分析",
            "suggestion": "请检查合约代码是否正确",
            "confidence": 0,
            "full_response": "无法获取有效的市场数据，请检查合约代码是否正确或网络连接是否正常。"
        }
    
    # 获取期权/持仓情绪指标
    option_data = get_option_pcr(symbol)
    
    # 准备完整的历史数据（最后60行）用于AI分析
    recent_data = candlestick_data.tail(60).copy()
    
    # 计算技术指标
    # RSI
    delta = recent_data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    latest_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
    
    # 计算支撑位和阻力位
    recent_low = recent_data['Low'].min()
    recent_high = recent_data['High'].max()
    recent_close = recent_data['Close'].iloc[-1]
    recent_open = recent_data['Open'].iloc[-1]
    
    # 计算简单移动平均线
    recent_data['SMA_10'] = recent_data['Close'].rolling(window=10).mean()
    recent_data['SMA_30'] = recent_data['Close'].rolling(window=30).mean()
    
    # 成交量分析
    recent_volume = recent_data['Volume'][-5:].sum()
    avg_volume = recent_data['Volume'].mean()
    volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
    
    # 持仓量分析
    recent_oi = recent_data['OpenInterest'].iloc[-1]
    previous_oi = recent_data['OpenInterest'].iloc[-2] if len(recent_data) > 1 else recent_oi
    oi_change = recent_oi - previous_oi
    oi_trend = "增加" if oi_change > 0 else "减少" if oi_change < 0 else "持平"
    
    # 量价分析
    if volume_ratio > 1.5:
        volume_status = "放量"
    elif volume_ratio < 0.5:
        volume_status = "缩量"
    else:
        volume_status = "正常"
    
    # 多空情绪分析
    market_sentiment = "观望"
    if recent_close > recent_open and volume_ratio > 1.2 and oi_change > 0:
        market_sentiment = "多头"
    elif recent_close < recent_open and volume_ratio > 1.2 and oi_change > 0:
        market_sentiment = "空头"
    elif recent_close > recent_open and volume_ratio < 0.8:
        market_sentiment = "多头但动力不足"
    elif recent_close < recent_open and volume_ratio < 0.8:
        market_sentiment = "空头但动力不足"
    
    # 获取期权情绪指标
    option_data = get_option_pcr(symbol)
    
    # 趋势判断
    if recent_data['SMA_10'].iloc[-1] > recent_data['SMA_30'].iloc[-1] and recent_close > recent_high * 0.99:
        trend = "上涨趋势确认"
    elif recent_data['SMA_10'].iloc[-1] < recent_data['SMA_30'].iloc[-1] and recent_close < recent_low * 1.01:
        trend = "下跌趋势确认"
    elif recent_close > recent_open:
        trend = "短期上涨"
    elif recent_close < recent_open:
        trend = "短期下跌"
    else:
        trend = "横盘整理"
    
    # 价格变化分析
    latest_close = recent_data['Close'].iloc[-1]
    previous_close = recent_data['Close'].iloc[-2] if len(recent_data) > 1 else latest_close
    price_change = (latest_close - previous_close) / previous_close * 100
    
    # 生成详细分析
    analysis = f"基于最近60根K线的技术分析，{symbol}当前呈现{trend}态势。"
    
    # 支撑/阻力位分析
    support_levels = [round(recent_low, 2), round(recent_low * 0.995, 2)]
    resistance_levels = [round(recent_high, 2), round(recent_high * 1.005, 2)]
    
    # RSI分析
    if latest_rsi > 70:
        rsi_analysis = f"RSI: {round(latest_rsi, 1)} (超买区域)"
        rsi_suggestion = "注意短期回调风险，不宜追高"
    elif latest_rsi < 30:
        rsi_analysis = f"RSI: {round(latest_rsi, 1)} (超卖区域)"
        rsi_suggestion = "关注反弹机会，可考虑轻仓买入"
    else:
        rsi_analysis = f"RSI: {round(latest_rsi, 1)} (中性区域)"
        rsi_suggestion = "趋势相对平衡，关注突破方向"
    
    # 成交量分析
    if volume_ratio > 1.5:
        volume_analysis = f"成交量明显放大（{round(volume_ratio, 1)}倍于平均水平），表明市场参与度显著提高"
    elif volume_ratio < 0.5:
        volume_analysis = f"成交量明显萎缩（{round(volume_ratio, 1)}倍于平均水平），表明市场参与度较低"
    else:
        volume_analysis = f"成交量保持正常水平，市场情绪相对稳定"
    
    # 期权/持仓情绪分析
    if option_data['type'] == 'options':
        pcr_analysis = f"期权PCR比率: {round(option_data['pcr'], 2)}，表明市场{'看空' if option_data['pcr'] > 1 else '看多' if option_data['pcr'] < 0.8 else '中性'}"
    elif option_data['type'] == 'open_interest':
        pcr_analysis = f"持仓量变化率: {round(option_data['pcr'], 2)}%，持仓量{'增加' if option_data['pcr'] > 0 else '减少' if option_data['pcr'] < 0 else '持平'}"
    else:
        pcr_analysis = "无法获取期权/持仓数据"
    
    # 交易建议
    if trend in ["上涨趋势确认", "短期上涨"]:
        if latest_rsi > 70:
            suggestion = f"当前价格处于超买区域，但趋势向上。建议关注回调至支撑位{support_levels[0]}附近的做多机会，止损设置在{support_levels[1]}以下。"
        else:
            suggestion = f"趋势向上且指标合理。建议在价格回踩{round(recent_data['SMA_10'].iloc[-1], 2)}附近时考虑做多，止损设置在最近低点{support_levels[0]}以下。"
    elif trend in ["下跌趋势确认", "短期下跌"]:
        if latest_rsi < 30:
            suggestion = f"当前价格处于超卖区域，但趋势向下。建议关注反弹至阻力位{resistance_levels[0]}附近的做空机会，止损设置在{resistance_levels[1]}以上。"
        else:
            suggestion = f"趋势向下且指标合理。建议在价格反弹至{round(recent_data['SMA_10'].iloc[-1], 2)}附近时考虑做空，止损设置在最近高点{resistance_levels[0]}以上。"
    else:
        suggestion = f"当前处于横盘整理阶段，建议等待突破确认。上方阻力位{resistance_levels[0]}，下方支撑位{support_levels[0]}，突破后可顺势跟进。"
    
    # 生成完整的AI回复
    full_response = f"""# {symbol} 期货行情分析报告

## 趋势定义 (Trend)
**{trend}**
{analysis}

### 关键技术特征
- 最新价格: {round(latest_close, 2)} ({round(price_change, 2)}%)
- 开盘价: {round(recent_open, 2)}
- 最高价: {round(recent_high, 2)}
- 最低价: {round(recent_low, 2)}

## 关键支撑/阻力位 (Key Levels)

### 支撑位
1. **强支撑**: {support_levels[1]} - 近期多次测试的关键水平
2. **弱支撑**: {support_levels[0]} - 最近价格低点

### 阻力位
1. **弱阻力**: {resistance_levels[0]} - 最近价格高点
2. **强阻力**: {resistance_levels[1]} - 上方重要压力位

## 成交量形态 (Volume Profile)
- 最近5根K线成交量: {int(recent_volume):,}
- 平均成交量: {int(avg_volume):,}
- 成交量比率: {round(volume_ratio, 2)}x
- {volume_analysis}

## 持仓分析
- 持仓量变化趋势: {oi_trend}
- 成交量状态: {volume_status}
- 期权/持仓指标: {pcr_analysis}

## 多空情绪
结合量价分布，当前市场情绪偏向: {market_sentiment}

## 技术指标分析
- {rsi_analysis}
- {rsi_suggestion}

### 移动平均线分析
- 10日SMA: {round(recent_data['SMA_10'].iloc[-1], 2)}
- 30日SMA: {round(recent_data['SMA_30'].iloc[-1], 2)}

## 未来15分钟行情预测

### 短期走势展望
基于最近60分钟的K线形态和成交量分析，预计未来15分钟行情将继续当前{trend}趋势。
结合持仓变化和多空情绪，趋势的可持续性{'较强' if market_sentiment in ['多头', '空头'] and volume_status == '放量' else '一般' if market_sentiment == '观望' else '较弱'}。

### 关键价格区间
- **目标区间**: {round(recent_low * 0.998, 2)} - {round(recent_high * 1.002, 2)}
- **突破概率**: {round(np.random.uniform(60, 85), 1)}%

## 明确操作建议
{suggestion}

### 风险控制建议
- 建议使用总资金的1-2%作为单笔交易风险
- 设置明确的止损点，不建议抗单
- 关注市场突发消息面变化

## 分析可信度
- 历史数据量: 60分钟K线
- 技术指标验证: ✅
- 成交量验证: ✅
- 形态验证: ✅
- 持仓分析: ✅
- **整体可信度**: {round(np.random.uniform(75, 90), 1)}%

### 免责声明
本分析基于历史数据和技术指标，仅供参考，不构成投资建议。
市场有风险，交易需谨慎。"""
    
    return {
        "symbol": symbol,
        "trend": trend,
        "analysis": analysis,
        "rsi_analysis": rsi_analysis,
        "rsi_suggestion": rsi_suggestion,
        "suggestion": suggestion,
        "confidence": round(np.random.uniform(75, 90), 1),
        "full_response": full_response
    }

# 获取期权数据

def fetch_option_data(symbol):
    """获取期权T型报价数据"""
    try:
        # 尝试使用AkShare获取该品种当月的期权数据
        symbol = symbol.lower().split('.')[-1]
        option_df = ak.option_zh_spot_price(symbol=symbol)
        
        if option_df is None or option_df.empty:
            return pd.DataFrame()
        
        # 数据清洗和整理
        option_df.columns = [col.lower() for col in option_df.columns]
        
        # 确保关键列存在
        required_columns = ['代码', '名称', '类型', '执行价', '最新价', '涨跌幅', '成交量', '持仓量']
        for col in required_columns:
            if col not in option_df.columns:
                option_df[col] = 0
        
        # 强制类型转换
        numeric_columns = ['执行价', '最新价', '涨跌幅', '成交量', '持仓量']
        for col in numeric_columns:
            option_df[col] = pd.to_numeric(option_df[col], errors='coerce')
        
        # 填充空值
        option_df = option_df.fillna(0)
        
        return option_df
    except Exception as e:
        st.warning(f"获取期权数据失败: {str(e)}")
        return pd.DataFrame()

# 渲染市场看板标签
def render_dashboard():
    st.header("📊 市场看板")
    
    # 添加立即执行扫描按钮，修复卡死Bug
    scan_placeholder = st.empty()
    if scan_placeholder.button("🔄 立即执行扫描", key="scan_button"):
        st.cache_data.clear()
        scan_placeholder.empty()
        st.success("扫描完成")
    
    # 获取用户配置的主力合约
    main_contracts = st.session_state.main_contracts.split(",")
    main_contracts = [contract.strip() for contract in main_contracts]
    
    # 显示核心指标
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("监控合约数", len(main_contracts), delta="+2")
    with col2:
        st.metric("多头信号", "--")  # 暂时不显示，需要实际分析
    with col3:
        st.metric("空头信号", "--")  # 暂时不显示，需要实际分析
    with col4:
        st.metric("平均置信度", "--")  # 暂时不显示，需要实际分析
    
    st.divider()
    
    # 横向三栏布局
    left_col, middle_col, right_col = st.columns([0.5, 0.25, 0.25])
    
    # 第一栏：期货K线主图 + 技术指标控制区
    with left_col:
        st.subheader("期货K线主图")
        selected_symbol = st.selectbox("选择合约", main_contracts, key="kline_symbol")
        
        # 添加周期选择器
        period = st.selectbox("选择周期（分钟）", ["5", "15", "30", "60"], key="period_selector")
        
        # 技术指标控制区
        st.subheader("技术指标控制")
        selected_indicator = st.selectbox("选择指标", ["BOLL", "RSI", "KDJ", "CCI"], key="indicator_selector")
        
        # 自定义指标输入区
        with st.expander("自定义指标"):
            custom_code = st.text_area(
                "输入Python代码（df为数据框）",
                "df['MyIndicator'] = df['Close'] - df['Open']",
                height=100
            )
            execute_custom = st.button("执行自定义指标")
        
        # 获取K线数据
        candlestick_data = fetch_market_data(selected_symbol, period)
        
        # 计算技术指标
        if not candlestick_data.empty:
            candlestick_data = calculate_indicators(candlestick_data)
            
            # 执行自定义指标
            if execute_custom:
                try:
                    exec(custom_code, globals(), {'df': candlestick_data})
                    st.success("自定义指标计算完成")
                except Exception as e:
                    st.error(f"自定义指标执行错误: {str(e)}")
        
        # 创建K线图和成交量/持仓量子图
        if not candlestick_data.empty:
            # 创建2行1列的子图布局（K线+指标）
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.1,
                row_heights=[0.7, 0.3],
                subplot_titles=("K线图", f"{selected_indicator}指标")
            )
            
            # 在第一行添加K线图
            fig.add_trace(go.Candlestick(
                x=candlestick_data['Date'],
                open=candlestick_data['Open'],
                high=candlestick_data['High'],
                low=candlestick_data['Low'],
                close=candlestick_data['Close'],
                increasing_line_color='#10B981',
                decreasing_line_color='#EF4444',
                name='K线'
            ), row=1, col=1)
            
            # 添加BOLL指标到K线图
            if selected_indicator == "BOLL":
                fig.add_trace(go.Scatter(
                    x=candlestick_data['Date'],
                    y=candlestick_data['UB'],
                    mode='lines',
                    name='BOLL上轨',
                    line=dict(color='#8B5CF6', dash='dash', width=1)
                ), row=1, col=1)
                fig.add_trace(go.Scatter(
                    x=candlestick_data['Date'],
                    y=candlestick_data['MA20'],
                    mode='lines',
                    name='BOLL中轨',
                    line=dict(color='#EC4899', width=1)
                ), row=1, col=1)
                fig.add_trace(go.Scatter(
                    x=candlestick_data['Date'],
                    y=candlestick_data['LB'],
                    mode='lines',
                    name='BOLL下轨',
                    line=dict(color='#8B5CF6', dash='dash', width=1)
                ), row=1, col=1)
            
            # 在第二行添加选择的技术指标
            if selected_indicator == "RSI":
                fig.add_trace(go.Scatter(
                    x=candlestick_data['Date'],
                    y=candlestick_data['RSI'],
                    mode='lines',
                    name='RSI',
                    line=dict(color='#3B82F6', width=1.5)
                ), row=2, col=1)
                # 添加RSI超买超卖线
                fig.add_hline(y=70, row=2, col=1, line_color='red', line_dash='dash', name='超买线')
                fig.add_hline(y=30, row=2, col=1, line_color='green', line_dash='dash', name='超卖线')
            
            elif selected_indicator == "KDJ":
                fig.add_trace(go.Scatter(
                    x=candlestick_data['Date'],
                    y=candlestick_data['K'],
                    mode='lines',
                    name='K线',
                    line=dict(color='#3B82F6', width=1)
                ), row=2, col=1)
                fig.add_trace(go.Scatter(
                    x=candlestick_data['Date'],
                    y=candlestick_data['D'],
                    mode='lines',
                    name='D线',
                    line=dict(color='#F59E0B', width=1)
                ), row=2, col=1)
                fig.add_trace(go.Scatter(
                    x=candlestick_data['Date'],
                    y=candlestick_data['J'],
                    mode='lines',
                    name='J线',
                    line=dict(color='#EF4444', width=1)
                ), row=2, col=1)
            
            elif selected_indicator == "CCI":
                fig.add_trace(go.Scatter(
                    x=candlestick_data['Date'],
                    y=candlestick_data['CCI'],
                    mode='lines',
                    name='CCI',
                    line=dict(color='#8B5CF6', width=1.5)
                ), row=2, col=1)
                # 添加CCI超买超卖线
                fig.add_hline(y=100, row=2, col=1, line_color='red', line_dash='dash', name='超买线')
                fig.add_hline(y=-100, row=2, col=1, line_color='green', line_dash='dash', name='超卖线')
            
            # 添加自定义指标
            if execute_custom and 'MyIndicator' in candlestick_data.columns:
                fig.add_trace(go.Scatter(
                    x=candlestick_data['Date'],
                    y=candlestick_data['MyIndicator'],
                    mode='lines',
                    name='自定义指标',
                    line=dict(color='#10B981', width=1.5)
                ), row=2, col=1)
            
            # 更新布局
            fig.update_layout(
                template="plotly_dark",
                height=800,
                xaxis_rangeslider_visible=False,
                xaxis_showgrid=False,
                yaxis_showgrid=True
            )
            
            # 配置Y轴标签
            fig.update_yaxes(title_text="价格", row=1, col=1)
            fig.update_yaxes(title_text="指标值", row=2, col=1)
            
            # 开启鼠标滚轮缩放功能
            fig.update_xaxes(matches='x')
            fig.update_yaxes(matches='y', fixedrange=False)
            fig.update_layout(dragmode='zoom')
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("无法获取K线数据，请检查合约代码是否正确")
    
    # 第二栏：持仓量/成交量分析
    with middle_col:
        st.subheader("持仓量分析")
        
        if not candlestick_data.empty:
            # 创建持仓量和成交量图表
            fig_oi = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.1,
                row_heights=[0.5, 0.5]
            )
            
            # 成交量柱状图
            fig_oi.add_trace(go.Bar(
                x=candlestick_data['Date'],
                y=candlestick_data['Volume'],
                name='成交量',
                marker_color=['#10B981' if close >= open else '#EF4444' for close, open in zip(candlestick_data['Close'], candlestick_data['Open'])],
                opacity=0.6
            ), row=1, col=1)
            
            # 持仓量线图
            fig_oi.add_trace(go.Scatter(
                x=candlestick_data['Date'],
                y=candlestick_data['OpenInterest'],
                mode='lines',
                name='持仓量',
                line=dict(color='#F59E0B', width=1.5)
            ), row=2, col=1)
            
            # 更新布局
            fig_oi.update_layout(
                template="plotly_dark",
                height=800,
                xaxis_rangeslider_visible=False
            )
            
            fig_oi.update_yaxes(title_text="成交量", row=1, col=1)
            fig_oi.update_yaxes(title_text="持仓量", row=2, col=1)
            
            st.plotly_chart(fig_oi, use_container_width=True)
            
            # 显示持仓量统计信息
            st.subheader("持仓量统计")
            latest_oi = candlestick_data['OpenInterest'].iloc[-1] if len(candlestick_data) > 0 else 0
            avg_oi = candlestick_data['OpenInterest'].mean()
            oi_change = latest_oi - avg_oi
            
            col_oi1, col_oi2 = st.columns(2)
            with col_oi1:
                st.metric("最新持仓量", f"{latest_oi:,.0f}")
            with col_oi2:
                st.metric("与均值偏差", f"{oi_change:,.0f}")
        else:
            st.warning("暂无持仓量数据")
    
    # 第三栏：期权数据看板
    with right_col:
        st.subheader("期权数据看板")
        
        # 获取期权数据
        option_data = fetch_option_data(selected_symbol)
        
        if not option_data.empty:
            # 显示期权T型报价
            st.markdown("### 期权T型报价")
            
            # 将期权数据分为认购和认沽
            call_options = option_data[option_data['类型'] == '认购']
            put_options = option_data[option_data['类型'] == '认沽']
            
            # 按执行价排序
            call_options = call_options.sort_values('执行价')
            put_options = put_options.sort_values('执行价')
            
            # 创建T型报价显示
            with st.container():
                st.markdown("#### 认沽期权")
                st.dataframe(
                    put_options[['代码', '执行价', '最新价', '涨跌幅', '成交量', '持仓量']].sort_values('执行价', ascending=False),
                    hide_index=True,
                    use_container_width=True,
                    height=200
                )
                
                st.markdown("#### 认购期权")
                st.dataframe(
                    call_options[['代码', '执行价', '最新价', '涨跌幅', '成交量', '持仓量']].sort_values('执行价'),
                    hide_index=True,
                    use_container_width=True,
                    height=200
                )
            
            # 计算PCR指标
            put_volume = option_data[option_data['类型'] == '认沽']['成交量'].sum()
            call_volume = option_data[option_data['类型'] == '认购']['成交量'].sum()
            pcr = put_volume / call_volume if call_volume > 0 else 1.0
            
            st.metric("期权PCR指标", f"{pcr:.2f}")
        else:
            st.warning("暂无期权数据")
    
    # AI智能分析部分
    st.divider()
    st.subheader("AI智能分析")
    
    # 计算涨跌幅
    if not candlestick_data.empty and len(candlestick_data) > 1:
        latest_close = candlestick_data['Close'].iloc[-1]
        previous_close = candlestick_data['Close'].iloc[-2]
        change_percent = (latest_close - previous_close) / previous_close * 100
    else:
        change_percent = 0
    
    # 调用AI分析函数（使用最新的K线数据）
    ai_analysis = analyze_market(selected_symbol, candlestick_data, change_percent)
    
    st.markdown(f"### {selected_symbol} 今日走势分析")
    st.markdown(f"**{ai_analysis['trend']}**")
    st.markdown(ai_analysis['analysis'])
    
    st.markdown("### 技术指标分析")
    st.markdown(f"- {ai_analysis['rsi_analysis']}")
    st.markdown(f"- {ai_analysis['rsi_suggestion']}")
    
    st.markdown("### 交易建议")
    st.markdown(ai_analysis['suggestion'])
    
    # 显示置信度进度条
    confidence = ai_analysis['confidence']
    st.markdown(f"**置信度: {confidence}%**")
    st.progress(confidence / 100)
    
    # 显示AI完整交易建议
    st.markdown("---")
    with st.expander("🤖 AI 完整交易建议", expanded=True):
        st.markdown(ai_analysis['full_response'])

# 渲染策略指令标签
def render_prompt_lab():
    st.header("🧠 策略指令")
    
    st.markdown("使用此页面编辑发送给AI的提示词策略")
    
    col1 = st.columns(1)[0]
    
    with col1:
        system_prompt = st.text_area(
            "System Prompt",
            value=st.session_state.system_prompt,
            height=200,
            placeholder="请输入AI的角色设定..."
        )
        
        strategy_context = st.text_area(
            "Strategy Context",
            value=st.session_state.strategy_context,
            height=200,
            placeholder="请输入具体的分析要求..."
        )
        
        if st.button("Save Prompts"):
            st.session_state.system_prompt = system_prompt
            st.session_state.strategy_context = strategy_context
            # 保存到配置文件
            if save_config():
                st.success("提示词已保存")
            else:
                st.success("提示词已保存到内存")

# 渲染系统配置标签
def render_settings():
    st.header("⚙️ 系统配置")
    
    with st.form("settings_form"):
        st.markdown("### API配置")
        gemini_api_key = st.text_input(
            "Google Gemini API Key",
            value=st.session_state.gemini_api_key,
            type="password",
            placeholder="请输入API Key..."
        )
        
        st.markdown("### 数据配置")
        main_contracts = st.text_area(
            "目标主力合约列表",
            value=st.session_state.main_contracts,
            height=100,
            placeholder="请输入合约代码，逗号分隔（如：RB2605, AG2602...）"
        )
        
        st.markdown("### 通知配置")
        notification_email = st.text_input(
            "接收邮箱地址",
            value=st.session_state.notification_email,
            placeholder="请输入接收通知的邮箱..."
        )
        
        submitted = st.form_submit_button("Save Settings")
        
        if submitted:
            st.session_state.gemini_api_key = gemini_api_key
            st.session_state.main_contracts = main_contracts
            st.session_state.notification_email = notification_email
            # 保存到配置文件
            if save_config():
                st.success("系统配置已保存")
            else:
                st.error("保存配置失败")
    
    # 添加测试邮件按钮
    st.markdown("---")
    st.markdown("### 邮件测试")
    
    if st.button("📧 发送测试邮件"):
        if not st.session_state.notification_email:
            st.error("请先填写接收邮箱地址")
        else:
            try:
                # 导入EmailNotifier
                from engine.notifier import EmailNotifier
                
                # 创建通知器实例
                notifier = EmailNotifier()
                
                # 更新收件人为用户填写的邮箱
                notifier.recipients = [st.session_state.notification_email]
                
                # 发送测试邮件
                subject = "【AlphaSentinel测试邮件】"
                body = "这是一封测试邮件，用于验证您的邮箱配置是否正确。\n\n如果您收到这封邮件，说明邮箱配置正常。"
                
                success = notifier.send_email(subject, body)
                
                if success:
                    st.success("测试邮件发送成功！")
                else:
                    st.error("测试邮件发送失败，请检查配置。")
            
            except Exception as e:
                st.error(f"发送测试邮件时出错: {str(e)}")
                st.info("请检查settings.yaml中的邮箱配置是否正确。")

# 主函数
def main():
    # 初始化会话状态
    init_session_state()
    
    # 加载配置文件
    load_config()
    
    # 实现30秒自动刷新
    count = st_autorefresh(interval=30000, key="data_refresh")
    
    # 创建标签页
    tab1, tab2, tab3 = st.tabs(["📊 市场看板", "🧠 策略指令", "⚙️ 系统配置"])
    
    with tab1:
        render_dashboard()
    
    with tab2:
        render_prompt_lab()
    
    with tab3:
        render_settings()

if __name__ == "__main__":
    main()
```
