import pandas as pd
import numpy as np

class backtest:
    def __init__(self, initial_cash: float, initial_weights: np.ndarray, restrictions: np.ndarray, expect_weights: np.ndarray, price: np.ndarray):
        self.initial_cash = initial_cash
        self.initial_weights = initial_weights
        self.restrictions = restrictions
        self.expect_weights = expect_weights
        self.price = price
    
    def run_backtest(self):
        change_weight = self.expect_weights - self.initial_weights
        change_weight[~self.restrictions] = 0
        stock_change_weights = change_weight[1:]
        stock_prices = self.price[1:]  

        buy_mask = stock_change_weights > 0
        buy_weights = stock_change_weights[buy_mask] 
        buy_prices = stock_prices[buy_mask]  

        theory_amounts = self.initial_cash * buy_weights  

        buy_shares = theory_amounts // buy_prices  

        actual_amounts = buy_shares * buy_prices 

        remainders = theory_amounts - actual_amounts  

# 加总所有买入金额
        total_buy_amount = actual_amounts.sum()  # 45000
        total_remainder = remainders.sum()  # 0

# 或者直接一步到位
        total_buy = np.sum((self.initial_cash * buy_weights) // buy_prices * buy_prices)

        print(f"总买入金额: {total_buy}")