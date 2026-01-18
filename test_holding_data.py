import sys
import os
import unittest
from datetime import datetime, timedelta

# 添加项目路径到sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dashboard_v6 import get_holding_rank_data

class TestHoldingData(unittest.TestCase):

    def test_get_latest_holding_data(self):
        """测试获取最新交易日的持仓数据"""
        # 测试品种：螺纹钢2505
        symbol = 'rb2505'
        data_type = '多单持仓'
        
        print(f"\n测试获取{symbol}的{data_type}数据...")
        df, data_date, error_msg = get_holding_rank_data(symbol, data_type)
        
        # 验证结果
        self.assertIsNotNone(data_date, "应该返回有效的数据日期")
        self.assertFalse(df.empty, "返回的数据不能为空")
        self.assertIsNone(error_msg, "不应该有错误信息")
        
        # 验证数据日期是最近的日期
        current_date = datetime.now()
        data_date_obj = datetime.strptime(data_date, '%Y%m%d')
        
        # 计算日期差（不包括今天，如果今天是交易日但数据还没更新）
        days_diff = (current_date - data_date_obj).days
        
        print(f"获取到{data_date}的持仓数据，距离今天{days_diff}天")
        
        # 检查数据日期是否是合理的交易日
        # 考虑到节假日可能导致较长的间隔，我们不设置固定天数限制
        # 而是检查数据日期是否是过去的日期
        self.assertLessEqual(data_date_obj, current_date, "数据日期应该是过去的日期")
        
        # 检查数据日期不是太早（例如不早于3个月前）
        three_months_ago = current_date - timedelta(days=90)
        self.assertGreaterEqual(data_date_obj, three_months_ago, "数据日期不应该早于3个月前")
        
        # 验证数据格式
        self.assertIn('名次', df.columns)
        self.assertIn('会员简称', df.columns)
        self.assertIn('数值', df.columns)
        self.assertIn('增减', df.columns)
        
        # 验证数据量
        self.assertGreaterEqual(len(df), 5, "应该至少有5条数据记录")
    
    def test_different_data_types(self):
        """测试获取不同类型的持仓数据"""
        symbol = 'rb2505'
        data_types = ['多单持仓', '空单持仓', '成交量排名']
        
        for data_type in data_types:
            print(f"\n测试获取{symbol}的{data_type}数据...")
            df, data_date, error_msg = get_holding_rank_data(symbol, data_type)
            
            self.assertIsNotNone(data_date, f"{data_type}应该返回有效的数据日期")
            self.assertFalse(df.empty, f"{data_type}返回的数据不能为空")
            self.assertIsNone(error_msg, f"{data_type}不应该有错误信息")
            self.assertGreaterEqual(len(df), 5, f"{data_type}应该至少有5条数据记录")

if __name__ == '__main__':
    unittest.main(verbosity=2)
