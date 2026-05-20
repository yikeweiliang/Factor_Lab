import pandas as pd
import numpy as np

class backtest:
    """This class aims to realize an absolutely safe package-modifying action. What you need to input is the current money, current weights, restrictions, expected weights and price. The output is the actual weights and shares after the modification."""
    def __init__(self, initial_money: float, initial_weights: np.ndarray, restrictions: np.ndarray, expect_weights: np.ndarray, price: np.ndarray):
        self.initial_money = initial_money
        self.initial_weights = initial_weights
        self.restrictions = restrictions
        self.expect_weights = expect_weights
        self.price = price
    
    def run_backtest_onetime(self):
        change_weight = self.expect_weights - self.initial_weights
        change_weight[~self.restrictions] = 0
        stock_change_weights = change_weight[1:]
        stock_actual_change_weight = np.zeros(len(stock_change_weights))
        stock_prices = self.price[1:]  
        current_cash = self.initial_money * self.initial_weights[0]

        sell_mask = stock_change_weights < 0
        sell_weights = - stock_change_weights[sell_mask] 
        sell_prices = stock_prices[sell_mask]  

        sell_shares = (self.initial_money * sell_weights) // sell_prices 

        actual_sell_amounts = sell_shares * sell_prices
        
        get_cash = np.sum(actual_sell_amounts)

        current_cash += get_cash

        stock_actual_change_weight[sell_mask] = -actual_sell_amounts / self.initial_money
        
        if current_cash > self.expect_weights[0] * self.initial_money:
            free_cash = current_cash - self.expect_weights[0] * self.initial_money
            buy_mask = stock_change_weights > 0
            buy_weights = stock_change_weights[buy_mask]
            buy_prices = stock_prices[buy_mask]
            if np.sum(buy_weights) > 0:
                buy_weights /= np.sum(buy_weights)
                buy_shares = buy_weights * free_cash // buy_prices
                actual_buy_amounts = buy_shares * buy_prices
                current_cash -= np.sum(actual_buy_amounts)
                actual_buy_change_weight = actual_buy_amounts / self.initial_money
            
                stock_actual_change_weight[buy_mask] = actual_buy_change_weight
        cash_weight = current_cash / self.initial_money
        current_weights = self.initial_weights.copy()
        current_weights[1:] += stock_actual_change_weight
        current_weights[0] = cash_weight
        current_shares = np.zeros(len(self.initial_weights))
        current_shares[1:] = (self.initial_money * current_weights[1:]) / stock_prices
        current_shares[0] = current_cash
        return current_weights, current_shares
    
class step_to_next_time:
    def __init__(self, current_shares: np.ndarray, price: np.ndarray):
        self.current_shares = current_shares
        self.price = price

    def step(self):
        current_values = self.current_shares.copy()
        current_values[1:] *= self.price[1:]
        current_money = np.sum(current_values)
        current_weights = current_values / current_money
        return current_money, current_weights









         
