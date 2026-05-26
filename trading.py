# 本质上就是拿到一张final表和一张price表，然后每次各取一行也就是一天的数据

# final表里一共有n+1列，第一列是日期，后面n列是n只股票的最终因子值
# price表里一共有n+1列，第一列是日期，后面n列是n只股票的价格
# 同时还需要输入初始资金initial_money，权重分配方法，tradingengine这个类的功能就是先从两张表里每次各取一行，然后根据权重分配方法计算出权重，然后跑回测

import pandas as pd
import numpy as np
from backtest import backtest, step_to_next_time
from weight_generation import weight_generation
class logwritter:
    def __init__(self, stock_list: list, output_path: str = 'daily_log.csv'):
        self.stock_list = stock_list
        self.output_path = output_path
        self.records = []

    def write(self, date: str, weights, shares, price):
        n = len(self.stock_list)
        stock_values = shares[1:] * price[1:]
        total_value = np.nansum(stock_values) + shares[0]
        row = {
            'date': date,
            'cash': shares[0],
            'total_value': total_value,
        }
        for i, name in enumerate(self.stock_list):
            row[f'{name}_shares'] = shares[i + 1]
            row[f'{name}_weight'] = weights[i + 1]
            row[f'{name}_value'] = stock_values[i]
        
        self.records.append(row)
    
    def save(self):
        df = pd.DataFrame(self.records)
        df.to_csv(self.output_path, index=False)
        print(f"持仓日志已经保存至：{self.output_path}")
        return df


class TradingEngine:
    def __init__(self,
                 stock_list: list,
                 final_table: pd.DataFrame,    # 列: [date, stock1, stock2, ...]
                 price_table: pd.DataFrame,    # 列: [date, stock1, stock2, ...]
                 volume_table: pd.DataFrame,   # 列: [date, stock1, stock2, ...]
                 initial_money: float,
                 weight_method: str = 'equal_weight',
                 log_path: str = 'daily_log.csv'):
        
        self.stock_list = stock_list
        self.final_table = final_table.set_index('date')
        self.price_table = price_table.set_index('date')
        self.volume_table = volume_table.set_index('date')
        self.initial_money = initial_money
        self.weight_method = weight_method
        self.log_writter = logwritter(stock_list, log_path)
    
    def run(self):
        n = len(self.stock_list)
        current_shares = np.zeros(n + 1)
        current_shares[0] = self.initial_money  # 全现金起步
        
        # 三张表日期取交集
        dates = self.final_table.index.intersection(
                    self.price_table.index
                ).intersection(self.volume_table.index)
        
        # 第0天数据作参考，从第1天开始交易
        for t in range(1, len(dates)):
            prev_date = dates[t-1]
            curr_date = dates[t]
            
            # 取当天数据
            factor_values = self.final_table.loc[curr_date].values       # shape (n,)
            curr_price_row = self.price_table.loc[curr_date].values      # shape (n,)
            prev_price_row = self.price_table.loc[prev_date].values      # shape (n,)
            volume_row = self.volume_table.loc[curr_date].values         # shape (n,)
            price = np.insert(curr_price_row, 0, 1.0)                    # shape (n+1,)
            
            # --- 生成 restrictions ---
            # 价格无效（NaN 或 0）→ 完全不能交易 (0)
            # 停牌：成交量为0 → 完全不能交易 (0)
            # 涨停：价格 >= 前收盘 * 1.099 → 不能买入 (-1)
            # 跌停：价格 <= 前收盘 * 0.901 → 不能卖出 (-2)
            # 正常：无限制 (1)
            restrict_arr = np.ones(n, dtype=int)  # 默认无限制

            # 价格无效或成交量为0 → 完全不能交易
            invalid_price = np.isnan(curr_price_row) | (curr_price_row == 0)
            restrict_arr[invalid_price] = 0
            restrict_arr[volume_row == 0] = 0

            # 只在价格有效 && 非停牌的前提下判断涨跌停
            valid_mask = ~invalid_price & (volume_row > 0)
            # 前收盘也需有效
            valid_prev = ~(np.isnan(prev_price_row) | (prev_price_row == 0))
            valid_mask = valid_mask & valid_prev

            restrict_arr[valid_mask & (curr_price_row >= prev_price_row * 1.099)] = -1   # 涨停
            restrict_arr[valid_mask & (curr_price_row <= prev_price_row * 0.901)] = -2   # 跌停

            restrictions = np.insert(restrict_arr, 0, 1)  # 现金永远无限制
            
            if t == 1:
                # 第1天：全现金建仓
                money = self.initial_money
                weights_before = np.zeros(n + 1)
                weights_before[0] = 1.0
            else:
                # 价格变动
                st = step_to_next_time(current_shares, price)
                money, weights_before = st.step()
            
            # 生成目标权重
            wg = weight_generation(self.stock_list, factor_values, self.weight_method)
            target_stock_weights = wg.get_weights()
            target = np.insert(target_stock_weights, 0, 0.0)  # 满仓，现金目标=0
            
            # 执行调仓
            bt = backtest(money, weights_before, restrictions, target, price)
            final_weights, current_shares = bt.run_backtest_onetime()
            
            # 记录日志
            self.log_writter.write(str(curr_date), final_weights, current_shares, price)
        
        return self.log_writter.save()



