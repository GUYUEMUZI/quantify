import os
import yaml
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# 导入自定义模块
from data.data_loader import DataLoader
from analysis.gemini_client import GeminiClient
from analysis.siliconflow_client import SiliconFlowClient
from analysis.technical_calc import TechnicalCalculator
from analysis.model_manager import get_model_manager, AIModel
from data.news_scraper import NewsScraper
from analysis.chart_plotter import ChartPlotter
from engine.notifier import EmailNotifier

# 导入数据获取函数
from data.data_utils import get_holding_rank_data, get_option_pcr

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StrategyManager:
    def __init__(self, config_path: str = None, custom_prompts: Dict[str, Any] = None):
        """
        初始化策略管理器
        :param config_path: 配置文件路径
        :param custom_prompts: 自定义提示词配置
        """
        # 加载配置
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), '../config/settings.yaml')
        self.config = self._load_config()
        
        # 初始化模型管理器
        self.model_manager = get_model_manager()
        
        # 初始化各个组件
        self.data_loader = DataLoader(rate_limit=self.config['data_loader']['rate_limit'])
        self.ai_client = self._create_ai_client(custom_prompts)
        self.tech_calculator = TechnicalCalculator()
        self.news_scraper = NewsScraper()
        self.chart_plotter = ChartPlotter()
        self.notifier = EmailNotifier(self.config_path)
        
        # 存储状态
        self.symbols_pool = self.data_loader.get_symbols_from_pool()
        self.top_5_symbols = []
        self.market_sentiment = None
        self.latest_analysis = {}
    
    def _create_ai_client(self, custom_prompts: Dict[str, Any] = None) -> Any:
        """
        根据当前活动模型创建AI客户端
        :param custom_prompts: 自定义提示词配置
        :return: AI客户端实例
        """
        active_model = self.model_manager.get_active_model()
        
        if not active_model:
            logger.warning("No active model found, using default SiliconFlow client")
            return SiliconFlowClient(custom_prompts=custom_prompts)
        
        if active_model.provider == 'siliconflow':
            return SiliconFlowClient(
                api_key=active_model.api_key,
                base_url=active_model.base_url,
                model=active_model.model_name,
                custom_prompts=custom_prompts
            )
        elif active_model.provider == 'gemini':
            return GeminiClient(
                api_key=active_model.api_key,
                custom_prompts=custom_prompts
            )
        else:
            logger.warning(f"Unknown provider: {active_model.provider}, using SiliconFlow as default")
            return SiliconFlowClient(custom_prompts=custom_prompts)
    
    def refresh_ai_client(self, custom_prompts: Dict[str, Any] = None):
        """
        刷新AI客户端（在模型切换后调用）
        :param custom_prompts: 自定义提示词配置
        """
        self.ai_client = self._create_ai_client(custom_prompts)
    
    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        :return: 配置字典
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def macro_analysis(self) -> Dict[str, Any]:
        """
        宏观定调：爬取新闻并分析宏观情绪
        :return: 宏观情绪分析结果
        """
        logger.info("Starting macro analysis...")
        
        try:
            # 爬取最新新闻
            news_list = self.news_scraper.get_latest_news()
            news_text = "\n".join(news_list)
            
            if not news_text:
                logger.warning("No news available for analysis")
                self.market_sentiment = {"sentiment_score": 0, "key_drivers": "无新闻数据", "impact_sectors": []}
                return self.market_sentiment
            
            # 分析新闻情绪
            self.market_sentiment = self.ai_client.analyze_news_sentiment(news_text)
            logger.info(f"Macro sentiment analysis completed: {self.market_sentiment}")
            
            return self.market_sentiment
        
        except Exception as e:
            logger.error(f"Failed to perform macro analysis: {e}")
            raise
    
    def market_scan(self) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        全量扫描：获取全市场期货数据
        :return: 多周期数据字典，格式为 {symbol: {period: data}}
        """
        logger.info(f"Starting market scan for {len(self.symbols_pool)} symbols...")
        
        try:
            # 获取多周期数据
            periods = ["60m", "30m", "15m", "5m"]
            market_data = self.data_loader.get_multiple_symbols_data(self.symbols_pool, periods)
            
            # 过滤掉没有数据的品种
            valid_symbols = {symbol: data for symbol, data in market_data.items() if any(p_data is not None for p_data in data.values())}
            
            logger.info(f"Market scan completed. Valid symbols: {len(valid_symbols)}")
            return valid_symbols
        
        except Exception as e:
            logger.error(f"Failed to perform market scan: {e}")
            raise
    
    def filter_symbols(self, market_data: Dict[str, Dict[str, pd.DataFrame]]) -> List[str]:
        """
        初筛：使用传统指标过滤品种
        :param market_data: 市场数据
        :return: 过滤后的品种列表
        """
        logger.info(f"Filtering symbols from {len(market_data)} candidates...")
        
        filtered_symbols = []
        filter_params = self.config['filter']
        
        for symbol, data_by_period in market_data.items():
            try:
                # 使用60分钟数据进行过滤
                if "60m" not in data_by_period or data_by_period["60m"] is None or data_by_period["60m"].empty:
                    continue
                
                df = data_by_period["60m"]
                
                # 计算技术指标
                df = self.tech_calculator.calculate_atr(df)
                df = self.tech_calculator.calculate_ma(df, window=20)
                
                # 检查交易量
                if df['volume'].iloc[-1] < filter_params['min_volume']:
                    continue
                
                # 检查ATR（波动率）
                if df['atr'].iloc[-1] < filter_params['min_atr']:
                    continue
                
                filtered_symbols.append(symbol)
                
                # 如果达到最大数量，停止过滤
                if len(filtered_symbols) >= filter_params['max_symbols']:
                    break
            
            except Exception as e:
                logger.warning(f"Error filtering symbol {symbol}: {e}")
                continue
        
        logger.info(f"Symbol filtering completed. {len(filtered_symbols)} symbols passed the filter")
        return filtered_symbols
    
    def deep_analysis(self, filtered_symbols: List[str], market_data: Dict[str, Dict[str, pd.DataFrame]]) -> Dict[str, Dict[str, Any]]:
        """
        深度分析：将初筛品种的数据发送给AI进行分析
        :param filtered_symbols: 过滤后的品种列表
        :param market_data: 市场数据
        :return: AI分析结果字典
        """
        logger.info(f"Starting deep analysis for {len(filtered_symbols)} symbols...")
        
        analysis_results = {}
        
        for symbol in filtered_symbols:
            try:
                # 获取该品种的多周期数据
                symbol_data = market_data[symbol]
                
                # 确保所有需要的周期都有数据
                if not all(period in symbol_data and symbol_data[period] is not None and not symbol_data[period].empty 
                          for period in ["60m", "30m", "15m", "5m"]):
                    continue
                
                # 获取持仓排名数据
                long_positions, long_date, long_error = get_holding_rank_data(symbol, data_type='多单持仓')
                short_positions, short_date, short_error = get_holding_rank_data(symbol, data_type='空单持仓')
                
                # 获取期权数据
                option_data = get_option_pcr(symbol)
                
                # 整合所有数据
                full_context = {
                    "market_sentiment": self.market_sentiment,
                    "option_data": option_data,
                    "holding_rank": {
                        "long_positions": long_positions.head(10).to_dict('records') if not long_positions.empty else [],
                        "short_positions": short_positions.head(10).to_dict('records') if not short_positions.empty else [],
                        "long_date": long_date,
                        "short_date": short_date
                    }
                }
                
                # AI分析交易策略
                strategy = self.ai_client.analyze_trading_strategy(symbol, symbol_data, full_context)
                
                # 生成图表
                chart_path = self.chart_plotter.plot_multiple_periods(symbol_data, symbol)
                strategy['chart_path'] = chart_path
                
                # 保存分析结果
                analysis_results[symbol] = strategy
                self.latest_analysis[symbol] = strategy
                
                logger.info(f"Deep analysis completed for {symbol}: {strategy['direction']} (strength: {strategy['signal_strength']})")
                
            except Exception as e:
                logger.error(f"Failed to perform deep analysis for {symbol}: {e}")
                continue
        
        logger.info(f"Deep analysis completed. Analyzed {len(analysis_results)} symbols")
        return analysis_results
    
    def select_top_5(self, analysis_results: Dict[str, Dict[str, Any]]) -> List[str]:
        """
        优选Top 5：根据AI评分和盈亏比排序
        :param analysis_results: AI分析结果
        :return: Top 5品种列表
        """
        logger.info("Selecting top 5 symbols...")
        
        # 过滤掉WAIT的策略
        actionable_strategies = {symbol: result for symbol, result in analysis_results.items() 
                               if result['direction'] != 'WAIT'}
        
        if not actionable_strategies:
            logger.warning("No actionable strategies found. Using all analyzed symbols.")
            actionable_strategies = analysis_results
        
        # 排序：首先按信号强度，然后按盈亏比
        sorted_symbols = sorted(
            actionable_strategies.items(),
            key=lambda x: (x[1]['signal_strength'], x[1]['rr_ratio']),
            reverse=True
        )
        
        # 选择Top 5
        self.top_5_symbols = [symbol for symbol, _ in sorted_symbols[:5]]
        
        logger.info(f"Top 5 symbols selected: {self.top_5_symbols}")
        return self.top_5_symbols
    
    def pre_market_scan(self) -> List[str]:
        """
        盘前扫描：执行完整的分析流程
        :return: Top 5品种列表
        """
        logger.info("Starting pre-market scan...")
        
        try:
            # 1. 宏观定调
            self.macro_analysis()
            
            # 2. 全量扫描
            market_data = self.market_scan()
            
            # 3. 初筛
            filtered_symbols = self.filter_symbols(market_data)
            
            # 4. 深度分析
            analysis_results = self.deep_analysis(filtered_symbols, market_data)
            
            # 5. 优选Top 5
            top_5 = self.select_top_5(analysis_results)
            
            # 6. 发送每日报告
            if top_5:
                report = {
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'market_sentiment': self.market_sentiment.get('key_drivers', '未知'),
                    'sentiment_score': self.market_sentiment.get('sentiment_score', 0),
                    'top_symbols': {symbol: analysis_results[symbol] for symbol in top_5 if symbol in analysis_results}
                }
                
                # 收集图表附件
                chart_paths = []
                for symbol in top_5:
                    if symbol in analysis_results and 'chart_path' in analysis_results[symbol]:
                        chart_paths.append(analysis_results[symbol]['chart_path'])
                
                # 发送报告
                self.notifier.send_daily_report(report, chart_paths)
            
            return top_5
            
        except Exception as e:
            logger.error(f"Pre-market scan failed: {e}")
            # 发送系统错误通知
            self.notifier.send_system_alert(f"盘前扫描失败: {str(e)}", "ERROR")
            raise
    
    def intraday_check(self) -> Dict[str, Dict[str, Any]]:
        """
        盘中跟踪：检查Top 5品种的实时情况
        :return: 实时分析结果
        """
        logger.info(f"Performing intraday check for Top 5 symbols: {self.top_5_symbols}")
        
        if not self.top_5_symbols:
            logger.warning("No top 5 symbols selected. Running pre-market scan first.")
            self.pre_market_scan()
            
            if not self.top_5_symbols:
                logger.error("Still no top 5 symbols after pre-market scan")
                return {}
        
        # 获取最新数据
        periods = ["5m", "15m"]  # 盘中主要关注短周期
        market_data = self.data_loader.get_multiple_symbols_data(self.top_5_symbols, periods)
        
        # 分析最新情况
        intraday_results = {}
        for symbol in self.top_5_symbols:
            try:
                if symbol not in market_data or not market_data[symbol]:
                    continue
                
                # 分析最新数据
                latest_strategy = self.ai_client.analyze_trading_strategy(symbol, market_data[symbol], self.market_sentiment)
                
                # 更新分析结果
                self.latest_analysis[symbol] = latest_strategy
                intraday_results[symbol] = latest_strategy
                
                logger.info(f"Intraday check for {symbol}: {latest_strategy['direction']} (strength: {latest_strategy['signal_strength']})")
                
                # 如果是有效的交易信号（LONG或SHORT），发送警报
                if latest_strategy['direction'] in ['LONG', 'SHORT']:
                    # 检查信号时间是否在15分钟内
                    latest_signal_time = latest_strategy.get('timestamp')
                    if latest_signal_time:
                        # 转换为datetime对象
                        if isinstance(latest_signal_time, str):
                            latest_signal_time = datetime.strptime(latest_signal_time, '%Y-%m-%d %H:%M:%S')
                        
                        # 使用Asia/Shanghai时区
                        import pytz
                        shanghai_tz = pytz.timezone('Asia/Shanghai')
                        current_time = datetime.now(shanghai_tz)
                        
                        # 确保latest_signal_time是带时区的
                        if latest_signal_time.tzinfo is None:
                            latest_signal_time = shanghai_tz.localize(latest_signal_time)
                        
                        # 检查是否在15分钟内
                        if latest_signal_time >= current_time - timedelta(minutes=15):
                            # 生成最新图表
                            chart_path = self.chart_plotter.plot_strategy_signals(market_data[symbol], latest_strategy)
                            
                            # 发送策略警报
                            self.notifier.send_strategy_alert(latest_strategy, [chart_path])
                        else:
                            logger.info(f"Signal for {symbol} is too old ({latest_signal_time}), skipping notification")
                
            except Exception as e:
                logger.error(f"Failed to perform intraday check for {symbol}: {e}")
                continue
        
        return intraday_results
    
    def get_latest_analysis(self, symbol: str = None) -> Dict[str, Any]:
        """
        获取最新分析结果
        :param symbol: 可选，指定品种
        :return: 分析结果
        """
        if symbol:
            return self.latest_analysis.get(symbol, {})
        return self.latest_analysis
    
    def get_top_5_symbols(self) -> List[str]:
        """
        获取当前Top 5品种
        :return: Top 5品种列表
        """
        return self.top_5_symbols
    
    def get_market_sentiment(self) -> Dict[str, Any]:
        """
        获取当前市场情绪
        :return: 市场情绪分析结果
        """
        return self.market_sentiment

# 测试代码
if __name__ == "__main__":
    try:
        strategy_manager = StrategyManager()
        
        # 测试盘前扫描
        top_5 = strategy_manager.pre_market_scan()
        print(f"Top 5 symbols: {top_5}")
        
        # 测试盘中跟踪
        if top_5:
            intraday_results = strategy_manager.intraday_check()
            print("Intraday results:")
            for symbol, result in intraday_results.items():
                print(f"  {symbol}: {result['direction']} (strength: {result['signal_strength']})")
                
    except Exception as e:
        print(f"Error: {e}")
