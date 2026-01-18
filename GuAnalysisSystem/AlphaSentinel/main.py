#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AlphaSentinel主程序入口
负责启动系统并调度任务
"""

import os
import logging
import sys
from datetime import datetime
from engine.strategy_manager import StrategyManager
from engine.scheduler import AlphaScheduler

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'logs', 'alpha_sentinel.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    主程序入口函数
    """
    logger.info("=" * 50)
    logger.info("AlphaSentinel 启动")
    logger.info(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)
    
    try:
        # 创建策略管理器实例
        strategy_manager = StrategyManager()
        
        # 创建调度器实例
        scheduler = AlphaScheduler(strategy_manager)
        
        # 设置调度任务
        scheduler.setup_scheduler()
        
        # 启动调度器
        scheduler.start()
        
        logger.info("AlphaSentinel 系统已启动，开始监控市场...")
        logger.info("按 Ctrl+C 停止系统")
        
        # 保持程序运行
        while True:
            pass
            
    except KeyboardInterrupt:
        logger.info("\nAlphaSentinel 系统已停止")
        sys.exit(0)
    except Exception as e:
        logger.error(f"AlphaSentinel 系统启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # 确保logs目录存在
    os.makedirs(os.path.join(os.path.dirname(__file__), 'logs'), exist_ok=True)
    # 确保db目录存在
    os.makedirs(os.path.join(os.path.dirname(__file__), 'db'), exist_ok=True)
    
    # 启动主程序
    main()
