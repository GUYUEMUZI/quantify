import mplfinance as mpf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import logging
from typing import List, Dict, Optional

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChartPlotter:
    def __init__(self, save_dir: str = "../logs/charts/"):
        """
        初始化图表生成器
        :param save_dir: 图表保存目录
        """
        self.save_dir = save_dir
        
        # 确保保存目录存在
        os.makedirs(self.save_dir, exist_ok=True)
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 默认样式配置
        self.default_style = mpf.make_mpf_style(
            base_mpf_style='charles',
            rc={'font.size': 8},
            gridcolor='lightgray',
            gridstyle='--',
            facecolor='white',
            edgecolor='lightgray'
        )
    
    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        预处理数据，确保格式符合mplfinance要求
        :param df: 原始数据
        :return: 预处理后的数据
        """
        # 复制数据以避免修改原始数据
        processed_df = df.copy()
        
        # 确保时间列是datetime类型
        if 'datetime' in processed_df.columns:
            processed_df['datetime'] = pd.to_datetime(processed_df['datetime'])
            processed_df.set_index('datetime', inplace=True)
        elif 'date' in processed_df.columns:
            processed_df['date'] = pd.to_datetime(processed_df['date'])
            processed_df.set_index('date', inplace=True)
        
        # 确保列名符合mplfinance要求
        column_mapping = {
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }
        processed_df.rename(columns=column_mapping, inplace=True)
        
        # 确保必要的列存在
        required_columns = ['Open', 'High', 'Low', 'Close']
        for col in required_columns:
            if col not in processed_df.columns:
                raise ValueError(f"缺少必要的列: {col}")
        
        return processed_df
    
    def plot_basic_kline(self, df: pd.DataFrame, symbol: str, period: str = "daily", 
                        title: Optional[str] = None) -> str:
        """
        绘制基础K线图
        :param df: 包含OHLCV数据的DataFrame
        :param symbol: 期货品种代码
        :param period: 时间周期
        :param title: 图表标题
        :return: 保存的图表文件路径
        """
        try:
            processed_df = self._preprocess_data(df)
            
            if title is None:
                title = f"{symbol} {period.upper()} K线图"
            
            # 保存图表文件路径
            filename = f"{symbol}_{period}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.save_dir, filename)
            
            # 绘制图表
            mpf.plot(
                processed_df,
                type='candle',
                style=self.default_style,
                title=title,
                ylabel='价格',
                volume=True,
                ylabel_lower='成交量',
                figratio=(16, 9),
                figscale=1.5,
                savefig=filepath
            )
            
            logger.info(f"基础K线图已保存: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"绘制基础K线图失败: {e}")
            raise
    
    def plot_with_indicators(self, df: pd.DataFrame, symbol: str, period: str = "daily", 
                           indicators: Optional[List[str]] = None, 
                           title: Optional[str] = None) -> str:
        """
        绘制带技术指标的K线图
        :param df: 包含OHLCV数据的DataFrame
        :param symbol: 期货品种代码
        :param period: 时间周期
        :param indicators: 要添加的指标列表，如['ma', 'macd', 'rsi', 'bbands']
        :param title: 图表标题
        :return: 保存的图表文件路径
        """
        try:
            processed_df = self._preprocess_data(df)
            
            if title is None:
                title = f"{symbol} {period.upper()} K线图及技术指标"
            
            # 默认指标
            if indicators is None:
                indicators = ['ma', 'macd', 'rsi']
            
            # 准备添加到图表中的指标
            add_plot = []
            
            # 添加MA指标
            if 'ma' in indicators:
                add_plot.append(mpf.make_addplot(processed_df['Close'].rolling(window=5).mean(), color='blue', width=0.7, label='MA5'))
                add_plot.append(mpf.make_addplot(processed_df['Close'].rolling(window=10).mean(), color='orange', width=0.7, label='MA10'))
                add_plot.append(mpf.make_addplot(processed_df['Close'].rolling(window=20).mean(), color='red', width=0.7, label='MA20'))
            
            # 添加MACD指标
            if 'macd' in indicators:
                # 计算MACD
                exp1 = processed_df['Close'].ewm(span=12, adjust=False).mean()
                exp2 = processed_df['Close'].ewm(span=26, adjust=False).mean()
                macd = exp1 - exp2
                signal = macd.ewm(span=9, adjust=False).mean()
                histogram = macd - signal
                
                add_plot.append(mpf.make_addplot(macd, panel=1, color='blue', width=0.7, label='MACD'))
                add_plot.append(mpf.make_addplot(signal, panel=1, color='red', width=0.7, label='Signal'))
                add_plot.append(mpf.make_addplot(histogram, panel=1, type='bar', color='dimgray', alpha=0.7))
            
            # 添加RSI指标
            if 'rsi' in indicators:
                # 计算RSI
                delta = processed_df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                
                add_plot.append(mpf.make_addplot(rsi, panel=2, color='purple', width=0.7, label='RSI'))
                # 添加RSI超买超卖线
                add_plot.append(mpf.make_addplot([70]*len(rsi), panel=2, color='red', linestyle='--', width=0.5))
                add_plot.append(mpf.make_addplot([30]*len(rsi), panel=2, color='green', linestyle='--', width=0.5))
            
            # 添加Bollinger Bands指标
            if 'bbands' in indicators:
                # 计算Bollinger Bands
                middle_band = processed_df['Close'].rolling(window=20).mean()
                std = processed_df['Close'].rolling(window=20).std()
                upper_band = middle_band + (std * 2)
                lower_band = middle_band - (std * 2)
                
                add_plot.append(mpf.make_addplot(upper_band, color='green', linestyle='--', width=0.7, label='Upper BB'))
                add_plot.append(mpf.make_addplot(lower_band, color='red', linestyle='--', width=0.7, label='Lower BB'))
            
            # 保存图表文件路径
            filename = f"{symbol}_{period}_indicators_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.save_dir, filename)
            
            # 绘制图表
            mpf.plot(
                processed_df,
                type='candle',
                style=self.default_style,
                title=title,
                ylabel='价格',
                volume=True,
                ylabel_lower='成交量',
                figratio=(16, 9),
                figscale=1.5,
                addplot=add_plot,
                savefig=filepath,
                panel_ratios=(4, 2, 2),  # 调整面板比例
                tight_layout=True
            )
            
            logger.info(f"带指标的K线图已保存: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"绘制带指标的K线图失败: {e}")
            raise
    
    def plot_strategy_signals(self, df: pd.DataFrame, symbol: str, strategy: Dict, 
                             period: str = "daily", title: Optional[str] = None) -> str:
        """
        绘制带有交易策略信号的K线图
        :param df: 包含OHLCV数据的DataFrame
        :param symbol: 期货品种代码
        :param strategy: 交易策略信息，包含入场点、止损点、止盈点等
        :param period: 时间周期
        :param title: 图表标题
        :return: 保存的图表文件路径
        """
        try:
            processed_df = self._preprocess_data(df)
            
            if title is None:
                title = f"{symbol} {period.upper()} 交易策略信号"
            
            # 准备添加到图表中的信号
            add_plot = []
            scatter_x = []
            scatter_y = []
            scatter_colors = []
            scatter_labels = []
            
            # 添加入场信号
            if 'entry_zone' in strategy and strategy['entry_zone']:
                entry_start = strategy['entry_zone'].get('price_start', strategy['entry_zone'].get('price'))
                entry_end = strategy['entry_zone'].get('price_end', strategy['entry_zone'].get('price'))
                entry_mid = (entry_start + entry_end) / 2
                
                # 找到最接近入场价格的K线
                closest_idx = (processed_df['Close'] - entry_mid).abs().idxmin()
                
                scatter_x.append(closest_idx)
                scatter_y.append(entry_mid)
                scatter_colors.append('limegreen' if strategy['direction'] == 'LONG' else 'red')
                scatter_labels.append('Entry')
                
                # 绘制入场区间
                if entry_start != entry_end:
                    add_plot.append(mpf.make_addplot([entry_start]*len(processed_df), color='limegreen', linestyle='--', alpha=0.5, width=0.5))
                    add_plot.append(mpf.make_addplot([entry_end]*len(processed_df), color='limegreen', linestyle='--', alpha=0.5, width=0.5))
            
            # 添加止损信号
            if 'stop_loss' in strategy and strategy['stop_loss']:
                stop_loss = strategy['stop_loss']
                
                # 绘制止损线
                add_plot.append(mpf.make_addplot([stop_loss]*len(processed_df), color='red', linestyle='--', alpha=0.7, width=0.7))
            
            # 添加止盈信号
            if 'targets' in strategy and strategy['targets']:
                for i, target in enumerate(strategy['targets']):
                    if 'price' in target:
                        target_price = target['price']
                        
                        # 绘制止盈线
                        color = 'green' if i == 0 else 'blue'
                        add_plot.append(mpf.make_addplot([target_price]*len(processed_df), color=color, linestyle='--', alpha=0.7, width=0.7))
            
            # 添加趋势线（如果有）
            if 'trend_lines' in strategy and strategy['trend_lines']:
                for line in strategy['trend_lines']:
                    if 'start' in line and 'end' in line:
                        # 这里需要更复杂的实现来绘制趋势线
                        pass
            
            # 保存图表文件路径
            filename = f"{symbol}_{period}_strategy_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.save_dir, filename)
            
            # 绘制图表
            fig, axlist = mpf.plot(
                processed_df,
                type='candle',
                style=self.default_style,
                title=title,
                ylabel='价格',
                volume=True,
                ylabel_lower='成交量',
                figratio=(16, 9),
                figscale=1.5,
                addplot=add_plot,
                returnfig=True,
                tight_layout=True
            )
            
            # 在主图表上添加策略信号标记
            if scatter_x:
                ax = axlist[0]
                ax.scatter(scatter_x, scatter_y, s=100, color=scatter_colors, marker='^' if strategy['direction'] == 'LONG' else 'v', alpha=0.8, edgecolor='black', linewidth=0.5)
                
                # 添加信号标签
                for x, y, label, color in zip(scatter_x, scatter_y, scatter_labels, scatter_colors):
                    ax.annotate(label, (x, y), xytext=(5, 5), textcoords='offset points', fontsize=9, color=color, weight='bold')
            
            # 保存图表
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close(fig)
            
            logger.info(f"带策略信号的K线图已保存: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"绘制带策略信号的K线图失败: {e}")
            raise
    
    def plot_multiple_periods(self, df_dict: Dict[str, pd.DataFrame], symbol: str,
                             title: Optional[str] = None) -> str:
        """
        绘制多个时间周期的K线图在同一个画布上
        :param df_dict: 包含不同时间周期数据的字典，格式为{period: df}
        :param symbol: 期货品种代码
        :param title: 图表标题
        :return: 保存的图表文件路径
        """
        try:
            if not df_dict:
                raise ValueError("至少需要一个时间周期的数据")
            
            if title is None:
                title = f"{symbol} 多周期K线图"
            
            # 预处理所有数据
            processed_dfs = {}
            for period, df in df_dict.items():
                processed_dfs[period] = self._preprocess_data(df)
            
            # 创建子图
            fig, axes = plt.subplots(nrows=len(processed_dfs), ncols=1, figsize=(16, 4*len(processed_dfs)))
            if len(processed_dfs) == 1:
                axes = [axes]  # 确保axes是列表
            
            # 绘制每个时间周期的K线图
            for i, (period, df) in enumerate(processed_dfs.items()):
                ax = axes[i]
                
                # 使用mplfinance绘制K线图
                mpf.plot(
                    df,
                    type='candle',
                    style=self.default_style,
                    ax=ax,
                    volume=False,
                    show_nontrading=False
                )
                
                ax.set_title(f"{period.upper()} K线图", fontsize=12, pad=10)
                ax.tick_params(axis='both', which='major', labelsize=10)
            
            # 设置主标题
            fig.suptitle(title, fontsize=16, y=0.98)
            
            # 调整布局
            plt.tight_layout()
            plt.subplots_adjust(top=0.95)
            
            # 保存图表文件路径
            filename = f"{symbol}_multiple_periods_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.save_dir, filename)
            
            # 保存图表
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close(fig)
            
            logger.info(f"多周期K线图已保存: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"绘制多周期K线图失败: {e}")
            raise
    
    def clear_old_charts(self, days: int = 7):
        """
        清理指定天数前的旧图表
        :param days: 保留最近几天的图表
        """
        try:
            cutoff_time = pd.Timestamp.now() - pd.Timedelta(days=days)
            
            for filename in os.listdir(self.save_dir):
                if filename.endswith('.png'):
                    filepath = os.path.join(self.save_dir, filename)
                    file_mtime = pd.Timestamp(os.path.getmtime(filepath), unit='s')
                    
                    if file_mtime < cutoff_time:
                        os.remove(filepath)
                        logger.info(f"已删除旧图表: {filepath}")
            
        except Exception as e:
            logger.error(f"清理旧图表失败: {e}")

# 测试代码
if __name__ == "__main__":
    import pandas as pd
    import numpy as np
    
    # 创建测试数据
    dates = pd.date_range('2023-01-01', periods=50, freq='D')
    close = np.random.randn(50).cumsum() + 100
    high = close + np.random.rand(50) * 2
    low = close - np.random.rand(50) * 2
    open = np.random.choice([high, low], size=50, replace=True) + np.random.randn(50) * 0.5
    volume = np.random.randint(1000, 10000, size=50)
    
    test_df = pd.DataFrame({
        'date': dates,
        'open': open,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })
    
    # 初始化图表生成器
    plotter = ChartPlotter()
    
    print("=== 测试基础K线图 ===")
    basic_path = plotter.plot_basic_kline(test_df, "TEST", "daily")
    print(f"基础K线图已保存到: {basic_path}")
    
    print("\n=== 测试带指标的K线图 ===")
    indicators_path = plotter.plot_with_indicators(test_df, "TEST", "daily", indicators=['ma', 'macd', 'rsi', 'bbands'])
    print(f"带指标的K线图已保存到: {indicators_path}")
    
    print("\n=== 测试带策略信号的K线图 ===")
    test_strategy = {
        'direction': 'LONG',
        'entry_zone': {'price_start': 95, 'price_end': 97},
        'stop_loss': 93,
        'targets': [{'level': 1, 'price': 100}, {'level': 2, 'price': 103}]
    }
    strategy_path = plotter.plot_strategy_signals(test_df, "TEST", test_strategy, "daily")
    print(f"带策略信号的K线图已保存到: {strategy_path}")
    
    print("\n=== 测试多周期K线图 ===")
    df_dict = {
        '60m': test_df.iloc[-20:],
        '30m': test_df.iloc[-30:],
        '15m': test_df.iloc[-40:]
    }
    multiple_path = plotter.plot_multiple_periods(df_dict, "TEST")
    print(f"多周期K线图已保存到: {multiple_path}")
