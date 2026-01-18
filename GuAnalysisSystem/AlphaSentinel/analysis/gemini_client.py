import google.generativeai as genai
import yaml
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self, api_key: str = None, prompts_config: str = None, custom_prompts: Dict[str, Any] = None):
        """
        初始化Gemini客户端
        :param api_key: Google Gemini API密钥
        :param prompts_config: 提示词配置文件路径
        :param custom_prompts: 自定义提示词配置（优先级高于配置文件）
        """
        # 加载API密钥
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key is required. Please provide it or set GEMINI_API_KEY environment variable.")
        
        # 配置Gemini
        genai.configure(api_key=self.api_key)
        
        # 加载提示词配置
        self.prompts_config = prompts_config or os.path.join(os.path.dirname(__file__), '../config/prompts.yaml')
        self.prompts = self._load_prompts()
        
        # 应用自定义提示词（如果提供）
        if custom_prompts:
            self.prompts.update(custom_prompts)
        
        # 创建模型实例
        self.model = genai.GenerativeModel('gemini-1.5-pro-latest')
    
    def _load_prompts(self) -> Dict[str, Any]:
        """
        从YAML文件加载提示词配置
        :return: 提示词配置字典
        """
        try:
            with open(self.prompts_config, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load prompts configuration: {e}")
            raise
    
    def _extract_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        从响应文本中提取JSON内容
        :param response_text: Gemini API的响应文本
        :return: 解析后的JSON字典
        """
        # 尝试找到JSON的开始和结束位置
        try:
            # 简单情况：整个响应就是JSON
            return json.loads(response_text)
        except json.JSONDecodeError:
            # 复杂情况：响应包含其他文本，需要提取JSON部分
            try:
                start_idx = response_text.index('{')
                end_idx = response_text.rindex('}') + 1
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            except (ValueError, json.JSONDecodeError) as e:
                logger.error(f"Failed to extract JSON from response: {response_text}")
                raise
    
    def analyze_news_sentiment(self, news_text: str) -> Dict[str, Any]:
        """
        分析新闻情绪
        :param news_text: 新闻文本
        :return: 包含情绪分析结果的字典
        """
        try:
            prompt = f"""{self.prompts['system_role']}

{self.prompts['news_strategy']['role']}
{self.prompts['news_strategy']['task']}

{news_text}

{self.prompts['news_strategy']['output_format']}
{self.prompts['news_strategy']['example_output']}
"""
            
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                return self._extract_json_response(response.text)
            else:
                raise ValueError("Empty response from Gemini API")
        
        except Exception as e:
            logger.error(f"Error analyzing news sentiment: {e}")
            raise
    
    def analyze_trading_strategy(self, symbol: str, market_data: Dict[str, Any], full_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析交易策略
        :param symbol: 期货品种代码
        :param market_data: 市场数据，格式为 {period: data}
        :param full_context: 完整上下文，包含宏观新闻、期权数据和持仓排名
        :return: 包含交易策略的字典
        """
        try:
            # 格式化市场数据为CSV格式
            formatted_data = """
# Market Data for Multiple Timeframes
"""
            
            for period, data in market_data.items():
                if data is not None and not data.empty:
                    formatted_data += f"\n\n## {period} timeframe data (last 50 candles)\n"
                    formatted_data += data.tail(50).to_csv(index=True)
            
            # 格式化宏观情绪
            news_context = full_context.get("market_sentiment", {})
            news_context_str = f"宏观情绪得分: {news_context.get('sentiment_score', 0)}, 主要驱动因素: {news_context.get('key_drivers', '')}, 受影响板块: {', '.join(news_context.get('impact_sectors', []))}"
            
            # 格式化期权数据
            option_data = full_context.get("option_data", {})
            if option_data and option_data.get("type") == "options":
                option_str = f"期权PCR比率: {round(option_data.get('pcr', 0), 2)}，表明市场{'看空' if option_data.get('pcr', 0) > 1 else '看涨' if option_data.get('pcr', 0) < 0.8 else '中性'}"
            else:
                option_str = "期权数据不可用"
            
            # 格式化持仓排名数据
            holding_rank = full_context.get("holding_rank", {})
            long_positions = holding_rank.get("long_positions", [])
            short_positions = holding_rank.get("short_positions", [])
            
            if long_positions and short_positions:
                holding_str = f"持仓排名数据显示，前10名多头持仓占比较{'高' if len(long_positions) > 5 else '低'}，前10名空头持仓占比较{'高' if len(short_positions) > 5 else '低'}"
            else:
                holding_str = "持仓排名数据不可用"
            
            prompt = f"""{self.prompts['system_role']}

{self.prompts['technical_strategy']['role']}
{self.prompts['technical_strategy']['objective']}

**Context:**
1. **宏观情绪:** {news_context_str} (利用此信息判断大趋势方向)
2. **期权市场:** {option_str} (利用此信息判断市场情绪)
3. **持仓排名:** {holding_str} (利用此信息判断主力资金流向)
4. **数据:** {formatted_data}

**Analysis Logic:**
{chr(10).join(f"{i+1}. {item}" for i, item in enumerate(self.prompts['technical_strategy']['analysis_logic']))}

**Constraints:**
{chr(10).join(f"- {item}" for item in self.prompts['technical_strategy']['constraints'])}

**Output Format (Strict JSON):**
{self.prompts['technical_strategy']['output_format']}
{self.prompts['technical_strategy']['example_output']}

请为品种 {symbol} 提供详细的交易策略分析。
"""
            
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                result = self._extract_json_response(response.text)
                # 确保返回的结果包含品种信息和时间戳
                result['symbol'] = symbol
                result['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return result
            else:
                raise ValueError("Empty response from Gemini API")
        
        except Exception as e:
            logger.error(f"Error analyzing trading strategy for {symbol}: {e}")
            raise
    
    def generate_chart_analysis(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成图表分析
        :param symbol: 期货品种代码
        :param market_data: 市场数据
        :return: 图表分析结果
        """
        try:
            # 只使用60分钟和30分钟数据进行图表分析
            relevant_periods = ['60m', '30m']
            formatted_data = ""
            
            for period in relevant_periods:
                if period in market_data and market_data[period] is not None and not market_data[period].empty:
                    formatted_data += f"\n\n## {period} timeframe data (last 100 candles)\n"
                    formatted_data += market_data[period].tail(100).to_csv(index=True)
            
            prompt = f"""{self.prompts['system_role']}

请分析以下 {symbol} 的K线数据，提供图表形态分析和关键点位识别。

{formatted_data}

**Output Format:** JSON
{
    "symbol": "品种名称",
    "chart_patterns": ["形态1", "形态2"],
    "key_support_levels": [价格1, 价格2],
    "key_resistance_levels": [价格1, 价格2],
    "trend_direction": "向上/向下/横盘",
    "volume_analysis": "成交量分析结果"
}
"""
            
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                return self._extract_json_response(response.text)
            else:
                raise ValueError("Empty response from Gemini API")
        
        except Exception as e:
            logger.error(f"Error generating chart analysis for {symbol}: {e}")
            raise

# 测试代码
if __name__ == "__main__":
    # 注意：需要设置环境变量 GEMINI_API_KEY 或者在初始化时提供
    try:
        client = GeminiClient()
        print("Gemini client initialized successfully.")
        
        # 测试新闻分析
        test_news = "美联储公布最新利率决议，维持联邦基金利率在5.25%-5.50%不变，符合市场预期。美联储主席鲍威尔表示，将继续关注通胀数据，不排除未来进一步加息的可能。国内方面，国家统计局公布的GDP数据显示，第三季度经济增长4.9%，高于预期。"
        news_result = client.analyze_news_sentiment(test_news)
        print("News sentiment analysis:", news_result)
        
    except Exception as e:
        print(f"Error: {e}")
