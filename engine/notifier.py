import smtplib
import ssl
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import formataddr
from typing import List, Dict, Optional
import yaml

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmailNotifier:
    def __init__(self, config_path: str = "../config/settings.yaml"):
        """
        初始化邮件通知器
        :param config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self._validate_config()
        
        # 设置SMTP服务器配置
        self.smtp_server = self.config['email']['smtp_server']
        self.smtp_port = self.config['email']['smtp_port']
        self.username = self.config['email']['username']
        self.password = self.config['email']['password']
        self.sender_name = self.config['email'].get('sender_name', 'AlphaSentinel')
        self.recipients = self.config['email']['recipient']
        
        # 如果收件人是单个字符串，转换为列表
        if isinstance(self.recipients, str):
            self.recipients = [self.recipients]
    
    def _load_config(self, config_path: str) -> Dict:
        """
        加载配置文件
        :param config_path: 配置文件路径
        :return: 配置字典
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise
    
    def _validate_config(self):
        """
        验证配置文件的完整性
        """
        required_fields = ['smtp_server', 'smtp_port', 'username', 'password', 'recipient']
        
        if 'email' not in self.config:
            raise ValueError("配置文件中缺少 'email' 部分")
        
        for field in required_fields:
            if field not in self.config['email']:
                raise ValueError(f"配置文件中缺少必要的邮件配置项: {field}")
    
    def _create_message(self, subject: str, body: str, html_body: Optional[str] = None,
                       attachments: Optional[List[str]] = None) -> MIMEMultipart:
        """
        创建邮件消息
        :param subject: 邮件主题
        :param body: 纯文本邮件正文
        :param html_body: HTML格式邮件正文
        :param attachments: 附件文件路径列表
        :return: 邮件消息对象
        """
        # 创建邮件消息
        message = MIMEMultipart()
        message['From'] = formataddr((self.sender_name, self.username))
        message['To'] = ", ".join(self.recipients)
        message['Subject'] = subject
        
        # 添加纯文本正文
        message.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # 添加HTML正文（如果提供）
        if html_body:
            message.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        # 添加附件（如果提供）
        if attachments:
            for attachment_path in attachments:
                try:
                    if os.path.exists(attachment_path):
                        with open(attachment_path, 'rb') as f:
                            part = MIMEApplication(f.read())
                            part.add_header('Content-Disposition', 'attachment', 
                                           filename=os.path.basename(attachment_path))
                            message.attach(part)
                        logger.info(f"已添加附件: {os.path.basename(attachment_path)}")
                    else:
                        logger.warning(f"附件文件不存在: {attachment_path}")
                except Exception as e:
                    logger.error(f"添加附件失败: {e}")
        
        return message
    
    def send_email(self, subject: str, body: str, html_body: Optional[str] = None,
                  attachments: Optional[List[str]] = None) -> bool:
        """
        发送邮件
        :param subject: 邮件主题
        :param body: 纯文本邮件正文
        :param html_body: HTML格式邮件正文
        :param attachments: 附件文件路径列表
        :return: 发送是否成功
        """
        try:
            # 创建邮件消息
            message = self._create_message(subject, body, html_body, attachments)
            
            # 发送邮件
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_port == 587:
                    # 使用STARTTLS加密
                    server.starttls(context=context)
                
                # 登录SMTP服务器
                server.login(self.username, self.password)
                
                # 发送邮件
                server.send_message(message)
            
            logger.info(f"邮件发送成功: {subject}")
            logger.info(f"收件人: {', '.join(self.recipients)}")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False
    
    def send_strategy_alert(self, strategy: Dict, chart_paths: Optional[List[str]] = None) -> bool:
        """
        发送交易策略警报邮件
        :param strategy: 交易策略信息
        :param chart_paths: 图表文件路径列表
        :return: 发送是否成功
        """
        try:
            # 构建邮件主题
            symbol = strategy.get('symbol', '未知品种')
            direction = strategy.get('direction', '未知方向')
            timestamp = strategy.get('timestamp', '未知时间')
            
            subject = f"【AlphaSentinel策略警报】{symbol} - {direction}信号 ({timestamp})"
            
            # 构建纯文本邮件正文
            plain_body = f"AlphaSentinel策略警报\n\n"
            plain_body += f"品种: {symbol}\n"
            plain_body += f"时间: {timestamp}\n"
            plain_body += f"方向: {direction}\n"
            plain_body += f"信号强度: {strategy.get('signal_strength', '未知')}\n"
            plain_body += f"盈亏比: {strategy.get('rr_ratio', '未知')}\n\n"
            
            if 'entry_zone' in strategy:
                entry = strategy['entry_zone']
                if isinstance(entry, dict):
                    if 'price_start' in entry and 'price_end' in entry:
                        plain_body += f"入场区间: {entry['price_start']} - {entry['price_end']}\n"
                    else:
                        plain_body += f"入场价格: {entry.get('price', '未知')}\n"
                else:
                    plain_body += f"入场价格: {entry}\n"
            
            if 'stop_loss' in strategy:
                plain_body += f"止损价格: {strategy['stop_loss']}\n"
            
            if 'targets' in strategy:
                plain_body += "止盈目标:\n"
                for i, target in enumerate(strategy['targets']):
                    plain_body += f"  目标{i+1}: {target.get('price', '未知')}\n"
            
            if 'reasoning' in strategy:
                plain_body += f"\n分析逻辑: {strategy['reasoning']}\n"
            
            if 'chart_pattern' in strategy:
                plain_body += f"图表形态: {strategy['chart_pattern']}\n"
            
            # 构建HTML邮件正文
            html_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}
                    .container {{ max-width: 800px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
                    h1 {{ color: #333; font-size: 24px; margin-bottom: 20px; }}
                    .alert {{ padding: 15px; margin-bottom: 20px; border-radius: 4px; }}
                    .alert-long {{ background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; }}
                    .alert-short {{ background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }}
                    .alert-wait {{ background-color: #fff3cd; border: 1px solid #ffeeba; color: #856404; }}
                    table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                    th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }}
                    th {{ background-color: #f2f2f2; font-weight: bold; }}
                    .reasoning {{ background-color: #f8f9fa; padding: 15px; border-radius: 4px; margin-top: 20px; }}
                    .footer {{ margin-top: 30px; font-size: 12px; color: #666; text-align: center; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>AlphaSentinel策略警报</h1>
                    
                    <div class="alert alert-{direction.lower()}">
                        <strong>{symbol} - {direction}信号</strong> ({timestamp})
                    </div>
                    
                    <table>
                        <tr>
                            <th>品种</th>
                            <td>{symbol}</td>
                        </tr>
                        <tr>
                            <th>时间</th>
                            <td>{timestamp}</td>
                        </tr>
                        <tr>
                            <th>方向</th>
                            <td>{direction}</td>
                        </tr>
                        <tr>
                            <th>信号强度</th>
                            <td>{strategy.get('signal_strength', '未知')}</td>
                        </tr>
                        <tr>
                            <th>盈亏比</th>
                            <td>{strategy.get('rr_ratio', '未知')}</td>
                        </tr>
                    </table>
                    
                    <h3>交易参数</h3>
                    <table>
                        <tr>
                            <th>入场</th>
                            <td>{self._format_entry(strategy.get('entry_zone'))}</td>
                        </tr>
                        <tr>
                            <th>止损</th>
                            <td>{strategy.get('stop_loss', '未知')}</td>
                        </tr>
                    </table>
                    
                    <h3>止盈目标</h3>
                    <table>
                        {self._format_targets(strategy.get('targets', []))}
                    </table>
                    
                    <div class="reasoning">
                        <h3>分析逻辑</h3>
                        <p>{strategy.get('reasoning', '暂无')}</p>
                        {f"<p><strong>图表形态:</strong> {strategy.get('chart_pattern', '暂无')}</p>" if 'chart_pattern' in strategy else ''}
                    </div>
                    
                    <div class="footer">
                        <p>此邮件由AlphaSentinel自动生成，请勿直接回复。</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 发送邮件
            return self.send_email(subject, plain_body, html_body, chart_paths)
            
        except Exception as e:
            logger.error(f"发送策略警报邮件失败: {e}")
            return False
    
    def _format_entry(self, entry_zone: Optional[Dict]) -> str:
        """
        格式化入场信息
        :param entry_zone: 入场区间信息
        :return: 格式化后的入场信息字符串
        """
        if not entry_zone:
            return "未知"
        
        if isinstance(entry_zone, dict):
            if 'price_start' in entry_zone and 'price_end' in entry_zone:
                return f"{entry_zone['price_start']} - {entry_zone['price_end']}"
            else:
                return str(entry_zone.get('price', '未知'))
        else:
            return str(entry_zone)
    
    def _format_targets(self, targets: List[Dict]) -> str:
        """
        格式化止盈目标信息
        :param targets: 止盈目标列表
        :return: 格式化后的止盈目标HTML字符串
        """
        if not targets:
            return "<tr><td colspan='2'>暂无</td></tr>"
        
        html = ""
        for i, target in enumerate(targets):
            price = target.get('price', '未知')
            level = target.get('level', i+1)
            html += f"<tr><th>目标{level}</th><td>{price}</td></tr>"
        
        return html
    
    def send_system_alert(self, message: str, level: str = "INFO") -> bool:
        """
        发送系统警报邮件
        :param message: 警报消息
        :param level: 警报级别（INFO, WARNING, ERROR）
        :return: 发送是否成功
        """
        subject = f"【AlphaSentinel系统警报】{level}"
        body = f"AlphaSentinel系统警报\n\n"
        body += f"级别: {level}\n"
        body += f"消息: {message}\n"
        
        return self.send_email(subject, body)
    
    def send_daily_report(self, report: Dict, chart_paths: Optional[List[str]] = None) -> bool:
        """
        发送每日分析报告邮件
        :param report: 每日报告信息
        :param chart_paths: 图表文件路径列表
        :return: 发送是否成功
        """
        try:
            # 构建邮件主题
            date = report.get('date', '未知日期')
            subject = f"【AlphaSentinel每日报告】{date}"
            
            # 构建纯文本邮件正文
            plain_body = f"AlphaSentinel每日报告\n\n"
            plain_body += f"日期: {date}\n"
            plain_body += f"宏观情绪: {report.get('market_sentiment', '未知')}\n"
            plain_body += f"情绪分数: {report.get('sentiment_score', '未知')}\n\n"
            
            if 'top_symbols' in report:
                plain_body += "今日关注品种:\n"
                for symbol, info in report['top_symbols'].items():
                    plain_body += f"  - {symbol}: {info.get('direction', '未知方向')}, 信号强度: {info.get('signal_strength', '未知')}\n"
            
            if 'market_summary' in report:
                plain_body += f"\n市场 summary: {report['market_summary']}\n"
            
            # 构建HTML邮件正文
            html_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}
                    .container {{ max-width: 800px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
                    h1 {{ color: #333; font-size: 24px; margin-bottom: 20px; }}
                    h2 {{ color: #555; font-size: 18px; margin-top: 25px; margin-bottom: 15px; }}
                    table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                    th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }}
                    th {{ background-color: #f2f2f2; font-weight: bold; }}
                    .summary {{ background-color: #e8f4f8; padding: 15px; border-radius: 4px; margin-bottom: 20px; }}
                    .symbol-list {{ list-style-type: none; padding: 0; }}
                    .symbol-list li {{ margin-bottom: 10px; padding: 10px; background-color: #f9f9f9; border-radius: 4px; }}
                    .footer {{ margin-top: 30px; font-size: 12px; color: #666; text-align: center; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>AlphaSentinel每日报告</h1>
                    
                    <div class="summary">
                        <h2>报告概览</h2>
                        <table>
                            <tr>
                                <th>日期</th>
                                <td>{date}</td>
                            </tr>
                            <tr>
                                <th>宏观情绪</th>
                                <td>{report.get('market_sentiment', '未知')}</td>
                            </tr>
                            <tr>
                                <th>情绪分数</th>
                                <td>{report.get('sentiment_score', '未知')}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <h2>今日关注品种</h2>
                    <ul class="symbol-list">
                        {self._format_daily_symbols(report.get('top_symbols', {}))}
                    </ul>
                    
                    {f"<h2>市场Summary</h2><p>{report.get('market_summary', '暂无')}</p>" if 'market_summary' in report else ''}
                    
                    <div class="footer">
                        <p>此邮件由AlphaSentinel自动生成，请勿直接回复。</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 发送邮件
            return self.send_email(subject, plain_body, html_body, chart_paths)
            
        except Exception as e:
            logger.error(f"发送每日报告邮件失败: {e}")
            return False
    
    def _format_daily_symbols(self, symbols: Dict) -> str:
        """
        格式化每日关注品种信息
        :param symbols: 品种信息字典
        :return: 格式化后的HTML字符串
        """
        if not symbols:
            return "<li>暂无推荐品种</li>"
        
        html = ""
        for symbol, info in symbols.items():
            direction = info.get('direction', '未知方向')
            strength = info.get('signal_strength', '未知')
            html += f"<li><strong>{symbol}</strong> - {direction} (信号强度: {strength})</li>"
        
        return html

# 测试代码
if __name__ == "__main__":
    import yaml
    import tempfile
    import os
    
    # 创建临时配置文件用于测试
    test_config = {
        'email': {
            'smtp_server': 'smtp.example.com',
            'smtp_port': 587,
            'username': 'test@example.com',
            'password': 'test_password',
            'recipient': 'recipient@example.com'
        }
    }
    
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        yaml.dump(test_config, f)
        temp_config_path = f.name
    
    try:
        # 初始化通知器（仅测试配置加载，不实际发送邮件）
        notifier = EmailNotifier(temp_config_path)
        print("通知器初始化成功")
        
        # 测试策略警报邮件构建（不实际发送）
        test_strategy = {
            'symbol': 'IF2301',
            'timestamp': '2023-01-01 09:30:00',
            'direction': 'LONG',
            'signal_strength': 85,
            'entry_zone': {'price_start': 4800, 'price_end': 4810},
            'stop_loss': 4780,
            'targets': [{'level': 1, 'price': 4850}, {'level': 2, 'price': 4900}],
            'rr_ratio': 2.5,
            'reasoning': '60分钟底背离，结合宏观利好，回踩5分钟MA20进场。',
            'chart_pattern': '上升三角形突破'
        }
        
        # 模拟发送邮件（实际不会发送，因为配置是假的）
        print("\n模拟发送策略警报邮件...")
        # notifier.send_strategy_alert(test_strategy)
        print("策略警报邮件模拟发送完成")
        
        # 测试每日报告邮件构建（不实际发送）
        test_report = {
            'date': '2023-01-01',
            'market_sentiment': '多头',
            'sentiment_score': 7,
            'top_symbols': {
                'IF2301': {'direction': 'LONG', 'signal_strength': 85},
                'SC2301': {'direction': 'SHORT', 'signal_strength': 75}
            },
            'market_summary': '今日市场整体呈多头趋势，IF2301和SC2301表现突出。'
        }
        
        print("\n模拟发送每日报告邮件...")
        # notifier.send_daily_report(test_report)
        print("每日报告邮件模拟发送完成")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    finally:
        # 删除临时配置文件
        os.unlink(temp_config_path)
        print(f"\n临时配置文件已删除: {temp_config_path}")
