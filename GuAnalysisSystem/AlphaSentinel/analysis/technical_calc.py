import pandas as pd
import numpy as np
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TechnicalCalculator:
    def __init__(self):
        """
        初始化技术指标计算器
        """
        pass
    
    def calculate_ma(self, df: pd.DataFrame, window: int = 20, column: str = 'close', name: str = None) -> pd.DataFrame:
        """
        计算移动平均线 (MA)
        :param df: 包含价格数据的DataFrame
        :param window: 计算窗口大小
        :param column: 用于计算的价格列
        :param name: 结果列的名称，如果为None则自动生成
        :return: 添加了MA指标的DataFrame
        """
        try:
            result_col = name or f'ma{window}'
            df[result_col] = df[column].rolling(window=window).mean()
            return df
        except Exception as e:
            logger.error(f"Failed to calculate MA with window {window}: {e}")
            raise
    
    def calculate_atr(self, df: pd.DataFrame, window: int = 14, name: str = 'atr') -> pd.DataFrame:
        """
        计算平均真实波幅 (ATR)
        :param df: 包含OHLC数据的DataFrame
        :param window: 计算窗口大小
        :param name: 结果列的名称
        :return: 添加了ATR指标的DataFrame
        """
        try:
            # 计算真实波幅
            df['tr1'] = df['high'] - df['low']
            df['tr2'] = abs(df['high'] - df['close'].shift(1))
            df['tr3'] = abs(df['low'] - df['close'].shift(1))
            df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
            
            # 计算ATR
            df[name] = df['tr'].rolling(window=window).mean()
            
            # 清理临时列
            df.drop(['tr1', 'tr2', 'tr3', 'tr'], axis=1, inplace=True)
            
            return df
        except Exception as e:
            logger.error(f"Failed to calculate ATR: {e}")
            raise
    
    def calculate_macd(self, df: pd.DataFrame, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9, 
                      column: str = 'close', prefix: str = 'macd') -> pd.DataFrame:
        """
        计算MACD指标
        :param df: 包含价格数据的DataFrame
        :param fast_period: 快速EMA周期
        :param slow_period: 慢速EMA周期
        :param signal_period: 信号线EMA周期
        :param column: 用于计算的价格列
        :param prefix: 结果列的前缀
        :return: 添加了MACD指标的DataFrame
        """
        try:
            # 计算EMA
            df[f'{prefix}_fast'] = df[column].ewm(span=fast_period, adjust=False).mean()
            df[f'{prefix}_slow'] = df[column].ewm(span=slow_period, adjust=False).mean()
            
            # 计算MACD线
            df[f'{prefix}_line'] = df[f'{prefix}_fast'] - df[f'{prefix}_slow']
            
            # 计算信号线
            df[f'{prefix}_signal'] = df[f'{prefix}_line'].ewm(span=signal_period, adjust=False).mean()
            
            # 计算柱状图
            df[f'{prefix}_hist'] = df[f'{prefix}_line'] - df[f'{prefix}_signal']
            
            return df
        except Exception as e:
            logger.error(f"Failed to calculate MACD: {e}")
            raise
    
    def calculate_rsi(self, df: pd.DataFrame, window: int = 14, column: str = 'close', name: str = 'rsi') -> pd.DataFrame:
        """
        计算相对强弱指标 (RSI)
        :param df: 包含价格数据的DataFrame
        :param window: 计算窗口大小
        :param column: 用于计算的价格列
        :param name: 结果列的名称
        :return: 添加了RSI指标的DataFrame
        """
        try:
            # 计算价格变动
            delta = df[column].diff()
            
            # 计算上涨和下跌
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            
            # 计算RS
            rs = gain / loss
            
            # 计算RSI
            df[name] = 100 - (100 / (1 + rs))
            
            return df
        except Exception as e:
            logger.error(f"Failed to calculate RSI: {e}")
            raise
    
    def calculate_bollinger_bands(self, df: pd.DataFrame, window: int = 20, num_std: float = 2.0, 
                                column: str = 'close', prefix: str = 'bb') -> pd.DataFrame:
        """
        计算布林带
        :param df: 包含价格数据的DataFrame
        :param window: 计算窗口大小
        :param num_std: 标准差倍数
        :param column: 用于计算的价格列
        :param prefix: 结果列的前缀
        :return: 添加了布林带指标的DataFrame
        """
        try:
            # 计算中轨 (MA)
            df[f'{prefix}_mid'] = df[column].rolling(window=window).mean()
            
            # 计算标准差
            std = df[column].rolling(window=window).std()
            
            # 计算上轨和下轨
            df[f'{prefix}_upper'] = df[f'{prefix}_mid'] + (std * num_std)
            df[f'{prefix}_lower'] = df[f'{prefix}_mid'] - (std * num_std)
            
            return df
        except Exception as e:
            logger.error(f"Failed to calculate Bollinger Bands: {e}")
            raise
    
    def calculate_volume_ma(self, df: pd.DataFrame, window: int = 20, column: str = 'volume', name: str = None) -> pd.DataFrame:
        """
        计算成交量移动平均线
        :param df: 包含成交量数据的DataFrame
        :param window: 计算窗口大小
        :param column: 成交量列
        :param name: 结果列的名称，如果为None则自动生成
        :return: 添加了成交量MA的DataFrame
        """
        try:
            result_col = name or f'vol_ma{window}'
            df[result_col] = df[column].rolling(window=window).mean()
            return df
        except Exception as e:
            logger.error(f"Failed to calculate volume MA with window {window}: {e}")
            raise
    
    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有常用技术指标
        :param df: 包含OHLCV数据的DataFrame
        :return: 添加了所有技术指标的DataFrame
        """
        try:
            df = self.calculate_ma(df, window=20)
            df = self.calculate_ma(df, window=50, name='ma50')
            df = self.calculate_ma(df, window=200, name='ma200')
            df = self.calculate_atr(df)
            df = self.calculate_macd(df)
            df = self.calculate_rsi(df)
            df = self.calculate_bollinger_bands(df)
            df = self.calculate_volume_ma(df)
            return df
        except Exception as e:
            logger.error(f"Failed to calculate all technical indicators: {e}")
            raise
    
    def calculate_position_size(self, total_capital: float, risk_per_trade: float, atr: float, contract_multiplier: float) -> float:
        """
        根据ATR计算建议开仓手数
        :param total_capital: 总资金
        :param risk_per_trade: 每笔交易的风险比例（0-1之间）
        :param atr: 平均真实波幅
        :param contract_multiplier: 合约乘数
        :return: 建议开仓手数
        """
        try:
            # 计算每手的风险金额
            risk_per_contract = atr * contract_multiplier
            
            # 计算可接受的总风险金额
            total_risk = total_capital * risk_per_trade
            
            # 计算手数
            position_size = total_risk / risk_per_contract
            
            # 向下取整，确保不超过风险限制
            return max(0.01, round(position_size, 2))
        except Exception as e:
            logger.error(f"Failed to calculate position size: {e}")
            raise

# 测试代码
if __name__ == "__main__":
    # 创建示例数据
    dates = pd.date_range('2023-01-01', periods=100)
    price = np.random.randn(100).cumsum() + 100
    high = price + np.random.rand(100) * 2
    low = price - np.random.rand(100) * 2
    close = price + np.random.randn(100) * 0.5
    volume = np.random.randint(1000, 10000, 100)
    
    df = pd.DataFrame({
        'date': dates,
        'open': price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })
    df.set_index('date', inplace=True)
    
    print("Original data:")
    print(df.head())
    
    # 测试技术指标计算
    calculator = TechnicalCalculator()
    
    print("\nCalculating MA...")
    df = calculator.calculate_ma(df, window=20)
    print(df['ma20'].tail())
    
    print("\nCalculating ATR...")
    df = calculator.calculate_atr(df)
    print(df['atr'].tail())
    
    print("\nCalculating MACD...")
    df = calculator.calculate_macd(df)
    print(df[['macd_line', 'macd_signal', 'macd_hist']].tail())
    
    print("\nCalculating RSI...")
    df = calculator.calculate_rsi(df)
    print(df['rsi'].tail())
    
    print("\nCalculating Bollinger Bands...")
    df = calculator.calculate_bollinger_bands(df)
    print(df[['bb_mid', 'bb_upper', 'bb_lower']].tail())
    
    print("\nCalculating all indicators...")
    df_all = calculator.calculate_all(df)
    print(df_all.columns)
