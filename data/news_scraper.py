import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from typing import List, Dict

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NewsScraper:
    def __init__(self):
        """
        初始化新闻爬虫
        """
        # 基础URL
        self.sina_finance_url = "https://finance.sina.com.cn/"
        self.eastmoney_url = "https://finance.eastmoney.com/"
        
        # 随机User-Agent列表，避免被封禁
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/89.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.64 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/89.0 Safari/537.36"
        ]
        
        # 初始请求头
        self.headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
            "Connection": "keep-alive"
        }
        
        # 爬取间隔（秒）
        self.crawl_interval = (1, 3)
    
    def _get_random_user_agent(self) -> str:
        """
        获取随机User-Agent
        :return: User-Agent字符串
        """
        return random.choice(self.user_agents)
    
    def _make_request(self, url: str) -> str:
        """
        发送HTTP请求，处理反爬机制
        :param url: 请求URL
        :return: 响应文本
        """
        try:
            # 更新User-Agent
            self.headers["User-Agent"] = self._get_random_user_agent()
            
            # 发送请求
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()  # 检查请求是否成功
            
            # 随机休眠，避免被封禁
            time.sleep(random.uniform(*self.crawl_interval))
            
            return response.text
        except Exception as e:
            logger.error(f"Failed to make request to {url}: {e}")
            return ""
    
    def _parse_sina_finance(self, html: str) -> List[str]:
        """
        解析新浪财经的新闻
        :param html: 网页HTML
        :return: 新闻列表
        """
        news_list = []
        
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # 解析头条新闻
            headline_news = soup.select(".top_newslist li a")
            for news in headline_news:
                title = news.get_text().strip()
                if title:
                    news_list.append(title)
            
            # 解析财经要闻
            important_news = soup.select(".blk_hd3 ul li a")
            for news in important_news:
                title = news.get_text().strip()
                if title:
                    news_list.append(title)
            
            # 解析滚动新闻
            scroll_news = soup.select(".list_009 li a")
            for news in scroll_news:
                title = news.get_text().strip()
                if title:
                    news_list.append(title)
            
        except Exception as e:
            logger.error(f"Failed to parse sina finance news: {e}")
        
        return news_list
    
    def _parse_eastmoney(self, html: str) -> List[str]:
        """
        解析东方财富的新闻
        :param html: 网页HTML
        :return: 新闻列表
        """
        news_list = []
        
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # 解析头条新闻
            headline_news = soup.select(".newsflash_ul li a")
            for news in headline_news:
                title = news.get_text().strip()
                if title:
                    news_list.append(title)
            
            # 解析要闻速递
            important_news = soup.select(".importantNews li a")
            for news in important_news:
                title = news.get_text().strip()
                if title:
                    news_list.append(title)
            
            # 解析财经聚焦
            focus_news = soup.select(".financeFocus li a")
            for news in focus_news:
                title = news.get_text().strip()
                if title:
                    news_list.append(title)
            
        except Exception as e:
            logger.error(f"Failed to parse eastmoney news: {e}")
        
        return news_list
    
    def get_latest_news(self, max_news: int = 50) -> List[str]:
        """
        获取最新的财经新闻
        :param max_news: 最大新闻数量
        :return: 新闻列表
        """
        logger.info("Starting to crawl latest financial news...")
        
        all_news = []
        
        try:
            # 爬取新浪财经
            sina_html = self._make_request(self.sina_finance_url)
            if sina_html:
                sina_news = self._parse_sina_finance(sina_html)
                all_news.extend(sina_news)
                logger.info(f"Crawled {len(sina_news)} news from Sina Finance")
            
            # 爬取东方财富
            eastmoney_html = self._make_request(self.eastmoney_url)
            if eastmoney_html:
                eastmoney_news = self._parse_eastmoney(eastmoney_html)
                all_news.extend(eastmoney_news)
                logger.info(f"Crawled {len(eastmoney_news)} news from Eastmoney")
            
            # 去重
            unique_news = list(dict.fromkeys(all_news))
            
            # 限制数量
            if len(unique_news) > max_news:
                unique_news = unique_news[:max_news]
            
            logger.info(f"Total unique news crawled: {len(unique_news)}")
            return unique_news
            
        except Exception as e:
            logger.error(f"Failed to get latest news: {e}")
            return []
    
    def get_news_with_content(self, max_news: int = 10) -> List[Dict[str, str]]:
        """
        获取新闻标题和内容（更深度的爬取）
        :param max_news: 最大新闻数量
        :return: 包含标题和内容的新闻列表
        """
        logger.info("Starting to crawl news with content...")
        
        # 注意：这个方法需要更复杂的实现，包括爬取新闻详情页
        # 由于反爬机制和网站结构可能经常变化，这里提供一个简化版本
        
        news_with_content = []
        basic_news = self.get_latest_news(max_news=max_news)
        
        for title in basic_news[:max_news]:
            news_with_content.append({
                "title": title,
                "content": "[内容爬取功能需要更复杂的实现，这里仅提供标题]",
                "source": "新浪财经/东方财富"
            })
        
        return news_with_content

# 测试代码
if __name__ == "__main__":
    scraper = NewsScraper()
    
    print("\n=== 测试新闻标题爬取 ===")
    news_list = scraper.get_latest_news(max_news=20)
    for i, news in enumerate(news_list):
        print(f"{i+1}. {news}")
    
    print("\n=== 测试新闻内容爬取 ===")
    news_with_content = scraper.get_news_with_content(max_news=5)
    for i, news in enumerate(news_with_content):
        print(f"{i+1}. 标题: {news['title']}")
        print(f"   内容: {news['content']}")
        print(f"   来源: {news['source']}")
        print()
