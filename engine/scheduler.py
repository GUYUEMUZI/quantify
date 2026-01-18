from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, time
import logging
import threading

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AlphaScheduler:
    def __init__(self, strategy_manager=None):
        """
        初始化调度器
        :param strategy_manager: 策略管理器实例
        """
        # 创建后台调度器
        self.scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
        self.running = False
        self.lock = threading.Lock()
        self.strategy_manager = strategy_manager
    
    def start(self):
        """
        启动调度器
        """
        with self.lock:
            if not self.running:
                try:
                    self.scheduler.start()
                    self.running = True
                    logger.info("Scheduler started successfully")
                except Exception as e:
                    logger.error(f"Failed to start scheduler: {e}")
                    raise
    
    def stop(self):
        """
        停止调度器
        """
        with self.lock:
            if self.running:
                try:
                    self.scheduler.shutdown()
                    self.running = False
                    logger.info("Scheduler stopped successfully")
                except Exception as e:
                    logger.error(f"Failed to stop scheduler: {e}")
                    raise
    
    def add_daily_task(self, task_func, hour: int, minute: int, args=None, kwargs=None):
        """
        添加每日定时任务
        :param task_func: 要执行的任务函数
        :param hour: 小时
        :param minute: 分钟
        :param args: 任务函数的位置参数
        :param kwargs: 任务函数的关键字参数
        :return: 任务ID
        """
        args = args or ()
        kwargs = kwargs or {}
        
        trigger = CronTrigger(hour=hour, minute=minute, timezone='Asia/Shanghai')
        job_id = self.scheduler.add_job(
            func=task_func,
            trigger=trigger,
            args=args,
            kwargs=kwargs,
            id=f"daily_{hour}_{minute}_{task_func.__name__}",
            replace_existing=True
        )
        
        logger.info(f"Added daily task {task_func.__name__} at {hour:02d}:{minute:02d}")
        return job_id.id
    
    def add_interval_task(self, task_func, minutes: int, args=None, kwargs=None, start_time=None, end_time=None):
        """
        添加间隔执行任务
        :param task_func: 要执行的任务函数
        :param minutes: 执行间隔（分钟）
        :param args: 任务函数的位置参数
        :param kwargs: 任务函数的关键字参数
        :param start_time: 开始时间
        :param end_time: 结束时间
        :return: 任务ID
        """
        args = args or ()
        kwargs = kwargs or {}
        
        # 创建间隔触发器
        trigger = IntervalTrigger(minutes=minutes, timezone='Asia/Shanghai')
        
        # 添加时间窗口限制（如果提供了开始和结束时间）
        job_kwargs = {}
        if start_time and end_time:
            job_kwargs['start_date'] = datetime.combine(datetime.now(), start_time)
            job_kwargs['end_date'] = datetime.combine(datetime.now(), end_time)
        
        job_id = self.scheduler.add_job(
            func=task_func,
            trigger=trigger,
            args=args,
            kwargs=kwargs,
            id=f"interval_{minutes}min_{task_func.__name__}",
            replace_existing=True,
            **job_kwargs
        )
        
        logger.info(f"Added interval task {task_func.__name__} with interval {minutes} minutes")
        return job_id.id
    
    def add_market_hours_task(self, task_func, minutes: int, args=None, kwargs=None):
        """
        添加盘内定时任务（9:00-11:30, 13:30-15:00, 21:00-02:30）
        :param task_func: 要执行的任务函数
        :param minutes: 执行间隔（分钟）
        :param args: 任务函数的位置参数
        :param kwargs: 任务函数的关键字参数
        :return: 任务ID列表
        """
        args = args or ()
        kwargs = kwargs or {}
        
        job_ids = []
        
        # 上午交易时段：9:00-11:30
        morning_start = time(9, 0)
        morning_end = time(11, 30)
        job_ids.append(self.add_interval_task(task_func, minutes, args, kwargs, morning_start, morning_end))
        
        # 下午交易时段：13:30-15:00
        afternoon_start = time(13, 30)
        afternoon_end = time(15, 0)
        job_ids.append(self.add_interval_task(task_func, minutes, args, kwargs, afternoon_start, afternoon_end))
        
        # 夜盘交易时段：21:00-02:30
        night_start = time(21, 0)
        night_end = time(2, 30)
        job_ids.append(self.add_interval_task(task_func, minutes, args, kwargs, night_start, night_end))
        
        return job_ids
    
    def remove_task(self, job_id):
        """
        移除指定任务
        :param job_id: 任务ID
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed task with ID: {job_id}")
        except Exception as e:
            logger.error(f"Failed to remove task {job_id}: {e}")
            raise
    
    def get_jobs(self):
        """
        获取所有任务
        :return: 任务列表
        """
        return self.scheduler.get_jobs()
    
    def print_jobs(self):
        """
        打印所有任务信息
        """
        self.scheduler.print_jobs()
    
    def run_now(self, task_func, args=None, kwargs=None):
        """
        立即执行指定任务
        :param task_func: 要执行的任务函数
        :param args: 任务函数的位置参数
        :param kwargs: 任务函数的关键字参数
        """
        args = args or ()
        kwargs = kwargs or {}
        
        try:
            logger.info(f"Running task {task_func.__name__} immediately")
            return task_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Failed to run task {task_func.__name__} immediately: {e}")
            raise
    
    def setup_scheduler(self):
        """
        设置调度任务
        """
        if not self.strategy_manager:
            logger.error("Strategy manager not provided, cannot set up scheduler")
            return
        
        logger.info("Setting up scheduled tasks...")
        
        # 添加每日任务
        self.add_daily_task(self.strategy_manager.macro_analysis, 8, 30)
        self.add_daily_task(self.strategy_manager.pre_market_scan, 8, 40)
        
        # 添加盘内定时任务
        self.add_market_hours_task(self.strategy_manager.intraday_check, 15)
        
        logger.info("All scheduled tasks have been set up")

# 测试代码
if __name__ == "__main__":
    def test_task(name):
        print(f"Test task {name} executed at {datetime.now()}")
    
    scheduler = AlphaScheduler()
    
    try:
        # 启动调度器
        scheduler.start()
        
        # 添加每日任务
        scheduler.add_daily_task(test_task, 8, 30, args=["news_crawl"])
        scheduler.add_daily_task(test_task, 8, 40, args=["market_scan"])
        
        # 添加盘内定时任务
        scheduler.add_market_hours_task(test_task, 15, args=["intraday_check"])
        
        # 立即执行任务
        scheduler.run_now(test_task, args=["immediate"])
        
        # 打印所有任务
        print("\nAll scheduled jobs:")
        scheduler.print_jobs()
        
        # 等待一段时间
        input("Press Enter to stop scheduler...")
        
    finally:
        # 停止调度器
        scheduler.stop()
