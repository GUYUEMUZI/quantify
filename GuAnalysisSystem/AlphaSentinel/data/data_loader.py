import akshare as ak
import time
import random
import pandas as pd
import os
import pickle
from datetime import datetime, timedelta

class DataLoader:
    def __init__(self, rate_limit=2, cache_dir=None):
        """
        初始化数据加载器
        :param rate_limit: 每秒请求次数限制
        :param cache_dir: 数据缓存目录
        """
        self.rate_limit = rate_limit
        self.cache_dir = cache_dir or os.path.join(os.path.dirname(__file__), '../cache')
        self.last_request_time = datetime.now()
        
        # 创建缓存目录
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _wait_for_rate_limit(self):
        """
        实现令牌桶算法，确保不超过请求频率限制
        """
        time_since_last_request = datetime.now() - self.last_request_time
        required_wait = 1.0 / self.rate_limit
        
        if time_since_last_request.total_seconds() < required_wait:
            wait_time = required_wait - time_since_last_request.total_seconds()
            time.sleep(wait_time)
        
        self.last_request_time = datetime.now()
    
    def _get_cache_path(self, symbol, period, date_str):
        """
        获取缓存文件路径
        :param symbol: 期货品种代码
        :param period: 周期
        :param date_str: 日期字符串
        :return: 缓存文件路径
        """
        return os.path.join(self.cache_dir, f"{symbol}_{period}_{date_str}.pkl")
    
    def _load_from_cache(self, symbol, period, max_age_hours=12):
        """
        从缓存加载数据
        :param symbol: 期货品种代码
        :param period: 周期
        :param max_age_hours: 缓存最大有效期（小时）
        :return: 缓存的数据，如果没有有效缓存则返回None
        """
        date_str = datetime.now().strftime("%Y%m%d")
        cache_path = self._get_cache_path(symbol, period, date_str)
        
        if os.path.exists(cache_path):
            cache_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
            if (datetime.now() - cache_time).total_seconds() < max_age_hours * 3600:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
        
        return None
    
    def _save_to_cache(self, data, symbol, period):
        """
        将数据保存到缓存
        :param data: 要缓存的数据
        :param symbol: 期货品种代码
        :param period: 周期
        """
        date_str = datetime.now().strftime("%Y%m%d")
        cache_path = self._get_cache_path(symbol, period, date_str)
        
        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)
    
    def get_futures_data(self, symbol, period="60m", adjust="qfq"):
        """
        获取期货数据，带有防封禁机制和缓存
        :param symbol: 期货品种代码
        :param period: 周期 (1m, 5m, 15m, 30m, 60m, daily, weekly, monthly)
        :param adjust: 复权类型 ("qfq": 前复权, "hfq": 后复权, "" 或 "None": 不复权)
        :return: 包含OHLCV数据的DataFrame
        """
        # 尝试从缓存加载
        cached_data = self._load_from_cache(symbol, period)
        if cached_data is not None:
            return cached_data
        
        # 遵守速率限制
        self._wait_for_rate_limit()
        
        # 随机休眠，模拟人类行为
        time.sleep(random.uniform(1.5, 3.0))
        
        try:
            # 获取期货数据
            if period in ["1m", "5m", "15m", "30m", "60m"]:
                # 分钟级数据
                df = ak.futures_zh_minute_sina(symbol=symbol, period=period)
            else:
                # 日线及以上数据
                df = ak.futures_zh_daily(symbol=symbol, adjust=adjust)
            
            # 保存到缓存
            self._save_to_cache(df, symbol, period)
            
            return df
        except Exception as e:
            print(f"Error fetching data for {symbol} ({period}): {e}")
            return None
    
    def get_multiple_symbols_data(self, symbols, periods=["60m", "30m", "15m", "5m"]):
        """
        获取多个品种的多周期数据
        :param symbols: 期货品种代码列表
        :param periods: 周期列表
        :return: 字典，格式为 {symbol: {period: data}}
        """
        results = {}
        
        for symbol in symbols:
            results[symbol] = {}
            for period in periods:
                data = self.get_futures_data(symbol, period)
                if data is not None:
                    results[symbol][period] = data
                
                # 额外休眠，进一步降低请求频率
                time.sleep(0.1)
        
        return results
    
    def get_symbols_from_pool(self, pool_file=None):
        """
        从品种池文件加载期货品种列表
        :param pool_file: 品种池文件路径
        :return: 期货品种列表
        """
        pool_file = pool_file or os.path.join(os.path.dirname(__file__), '../config/symbols_pool.txt')
        
        symbols = []
        try:
            with open(pool_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        symbols.append(line)
        except Exception as e:
            print(f"Error loading symbols pool: {e}")
        
        return symbols

# 测试代码
if __name__ == "__main__":
    loader = DataLoader(rate_limit=2)
    
    # 测试单个品种数据获取
    print("Testing single symbol data fetch...")
    symbol = "螺纹钢"
    data = loader.get_futures_data(symbol, period="60m")
    if data is not None:
        print(f"Successfully fetched {symbol} 60m data:")
        print(data.head())
    
    # 测试品种池加载
    print("\nTesting symbols pool loading...")
    symbols = loader.get_symbols_from_pool()
    print(f"Loaded {len(symbols)} symbols from pool")
    print(symbols[:5])
