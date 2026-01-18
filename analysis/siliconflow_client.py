import yaml
import os
import json
import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SiliconFlowClient:
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None, prompts_config: str = None, custom_prompts: Dict[str, Any] = None):
        """
        初始化硅基流动客户端
        :param api_key: SiliconFlow API密钥
        :param base_url: SiliconFlow API基础URL
        :param model: 使用的模型名称
        :param prompts_config: 提示词配置文件路径
        :param custom_prompts: 自定义提示词配置（优先级高于配置文件）
        """
        self.api_key = api_key or os.environ.get('SILICONFLOW_API_KEY')
        
        # 验证API密钥
        if not self.api_key:
            logger.error("SILICONFLOW_API_KEY is not set in environment variables or provided as parameter")
            raise ValueError("SILICONFLOW_API_KEY is required")
        
        self.base_url = base_url or "https://api.siliconflow.cn/v1"
        self.model = model or "deepseek-ai/DeepSeek-V3.2"
        
        # 设置请求头
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 日志记录配置信息
        logger.info(f"SiliconFlowClient initialized with: model={self.model}, base_url={self.base_url}")
        
        # 加载提示词配置
        self.prompts_config = prompts_config or os.path.join(os.path.dirname(__file__), '../config/prompts.yaml')
        self.prompts = self._load_prompts()
        
        # 应用自定义提示词（如果提供）
        if custom_prompts:
            self.prompts.update(custom_prompts)
    
    def _load_prompts(self) -> Dict[str, Any]:
        """
        从YAML文件加载提示词配置
        :return: 提示词配置字典
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(self.prompts_config):
                logger.error(f"Prompts configuration file not found: {self.prompts_config}")
                raise FileNotFoundError(f"Prompts configuration file not found: {self.prompts_config}")
            
            # 检查文件是否为空
            if os.path.getsize(self.prompts_config) == 0:
                logger.error(f"Prompts configuration file is empty: {self.prompts_config}")
                raise ValueError(f"Prompts configuration file is empty: {self.prompts_config}")
            
            with open(self.prompts_config, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
                # 检查加载的配置是否有效
                if config is None:
                    logger.error(f"Failed to parse YAML file: {self.prompts_config}")
                    raise ValueError(f"Failed to parse YAML file: {self.prompts_config}")
                
                return config
        except Exception as e:
            logger.error(f"Failed to load prompts configuration: {type(e).__name__} - {str(e)}")
            raise
    
    def _generate_content(self, prompt: str) -> str:
        """
        调用硅基流动API生成内容
        :param prompt: 提示词
        :return: 生成的文本内容
        """
        try:
            # 构建请求体
            request_body = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            # 配置重试策略
            from urllib3.util.retry import Retry
            from requests.adapters import HTTPAdapter
            
            # 创建会话
            session = requests.Session()
            
            # 设置重试策略
            retry_strategy = Retry(
                total=3,  # 总重试次数
                backoff_factor=1,  # 重试间隔因子
                status_forcelist=[429, 500, 502, 503, 504],  # 需要重试的状态码
                allowed_methods=["POST"]  # 允许重试的HTTP方法
            )
            
            # 设置适配器
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            
            # 发送HTTP请求到硅基流动API的聊天完成端点
            response = session.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=request_body,
                timeout=120  # 设置超时时间
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应并返回生成的文本内容
            response_data = response.json()
            return response_data["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout Error when generating content: {e}")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error when generating content: {e.response.status_code} - {e.response.reason}")
            logger.error(f"Response content: {e.response.content}")
            raise
        except Exception as e:
            logger.error(f"Failed to generate content: {type(e).__name__} - {str(e)}")
            raise
    
    def _extract_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        从响应文本中提取JSON内容
        :param response_text: API的响应文本
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
            
            response_text = self._generate_content(prompt)
            return self._extract_json_response(response_text)
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
            
            # 验证持仓数据格式
            def validate_holding_data(data):
                """验证持仓数据格式是否正确"""
                if not data or not isinstance(data, list):
                    return []
                # 过滤有效数据：确保每个元素是字典，且包含必要的键
                valid_data = []
                for item in data:
                    if isinstance(item, dict) and '会员简称' in item and '数值' in item:
                        valid_data.append(item)
                return valid_data
            
            # 验证并过滤持仓数据
            valid_long_positions = validate_holding_data(long_positions)
            valid_short_positions = validate_holding_data(short_positions)
            
            if valid_long_positions and valid_short_positions:
                holding_str = f"持仓排名数据显示，前10名多头持仓占比较{'高' if len(valid_long_positions) > 5 else '低'}，前10名空头持仓占比较{'高' if len(valid_short_positions) > 5 else '低'}"
            else:
                holding_str = "持仓排名数据不可用"
            
            # 构建详细的提示词，包含所有要求的数据源
            prompt = f"""{self.prompts['system_role']}

{self.prompts['technical_strategy']['role']}
{self.prompts['technical_strategy']['objective']}

**分析数据源：**
1. **K线数据（多周期）:**
{formatted_data}

2. **合约持仓排名数据:**
- 多头持仓排名: {', '.join([f"{item['会员简称']} ({item['数值']})" for item in valid_long_positions[:5]]) if valid_long_positions else '无数据'}
- 空头持仓排名: {', '.join([f"{item['会员简称']} ({item['数值']})" for item in valid_short_positions[:5]]) if valid_short_positions else '无数据'}

3. **期权市场数据:**
{option_str}

4. **宏观市场情绪:**
{news_context_str}

**分析逻辑：**
{chr(10).join(f"{i+1}. {item}" for i, item in enumerate(self.prompts['technical_strategy']['analysis_logic']))}

**交易约束：**
{chr(10).join(f"- {item}" for item in self.prompts['technical_strategy']['constraints'][:-1])}  # 移除JSON格式约束

请为品种 {symbol} 提供详细的交易策略分析，包含技术分析、基本面分析、风险提示和操作建议。

分析结果应尽可能详细，覆盖以下方面：
- 市场趋势判断
- 关键支撑和阻力位
- 技术指标解读
- 持仓结构分析
- 市场情绪评估
- 交易机会识别
- 风险管理建议

请使用流畅的自然语言进行分析，以专业分析师的口吻呈现全面的市场分析和交易建议，避免使用预设模板或强制格式要求。
"""
            
            # 优化AI分析结果生成速度
            request_body = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 3000,  # 增加token限制，支持更详细的分析
                "top_p": 0.9,  # 使用top_p采样，提高生成质量
                "frequency_penalty": 0.1,  # 减少重复内容
                "presence_penalty": 0.1  # 增加新内容
            }
            
            # 配置重试策略
            from urllib3.util.retry import Retry
            from requests.adapters import HTTPAdapter
            
            # 创建会话
            session = requests.Session()
            
            # 设置重试策略
            retry_strategy = Retry(
                total=3,  # 总重试次数
                backoff_factor=1,  # 重试间隔因子
                status_forcelist=[429, 500, 502, 503, 504],  # 需要重试的状态码
                allowed_methods=["POST"]  # 允许重试的HTTP方法
            )
            
            # 设置适配器
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            
            try:
                response = session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=request_body,
                    timeout=120  # 增加超时时间到120秒
                )
                
                # 详细记录请求和响应信息以帮助调试
                logger.info(f"API Request: URL={self.base_url}/chat/completions, Model={self.model}, Status Code={response.status_code}")
                
                # 检查响应状态
                response.raise_for_status()
                
                # 解析响应
                response_data = response.json()
                logger.info(f"API Response: Keys={list(response_data.keys())}")
                
                # 获取生成的文本内容
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    if "message" in response_data["choices"][0] and "content" in response_data["choices"][0]["message"]:
                        response_text = response_data["choices"][0]["message"]["content"]
                        logger.info(f"Generated Content Length: {len(response_text)} characters")
                    else:
                        logger.error(f"Unexpected response structure: {response_data}")
                        raise ValueError(f"API returned unexpected response structure: {response_data}")
                else:
                    logger.error(f"No choices in response: {response_data}")
                    raise ValueError(f"API returned no choices: {response_data}")
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP Error: {e.response.status_code} - {e.response.reason}")
                logger.error(f"Response content: {e.response.content}")
                raise
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection Error: {e}")
                raise
            except requests.exceptions.Timeout as e:
                logger.error(f"Timeout Error: {e}")
                raise
            except json.JSONDecodeError as e:
                logger.error(f"JSON Decode Error: {e}")
                logger.error(f"Response content: {response.content}")
                raise
            except Exception as e:
                logger.error(f"Failed to generate content: {type(e).__name__} - {str(e)}")
                raise
            
            # 构建结果字典
            # 确保包含full_response字段以兼容dashboard_v6.py的检查
            result = {
                'symbol': symbol,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'analysis_content': response_text,  # 原始分析内容
                'full_response': response_text,  # 兼容原有代码
                'market_data_sources': {
                    'kline_data': list(market_data.keys()),
                    'holding_rank_available': bool(long_positions and short_positions),
                    'option_data_available': bool(option_data and option_data.get('type') == 'options'),
                    'news_sentiment_available': bool(news_context)
                }
            }
            return result
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
            
            response_text = self._generate_content(prompt)
            return self._extract_json_response(response_text)
        except Exception as e:
            logger.error(f"Error generating chart analysis for {symbol}: {e}")
            raise

# 测试代码
if __name__ == "__main__":
    # 注意：需要设置环境变量 SILICONFLOW_API_KEY 或者在初始化时提供
    try:
        client = SiliconFlowClient()
        print("SiliconFlow client initialized successfully.")
        
        # 测试新闻分析
        test_news = "美联储公布最新利率决议，维持联邦基金利率在5.25%-5.50%不变，符合市场预期。美联储主席鲍威尔表示，将继续关注通胀数据，不排除未来进一步加息的可能。国内方面，国家统计局公布的GDP数据显示，第三季度经济增长4.9%，高于预期。"
        news_result = client.analyze_news_sentiment(test_news)
        print("News sentiment analysis:", news_result)
        
    except Exception as e:
        print(f"Error: {e}")