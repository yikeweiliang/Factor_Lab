import pandas as pd
import numpy as np

# 模块级注册表
_method_registry = {}

def register_method(method_name):
    def decorator(func):
        _method_registry[method_name] = func
        return func
    return decorator


class weight_generation:

    def __init__(self, stock_list: list, final_score: np.ndarray, method: str):
        self.length = len(stock_list)
        self.method = method
        self.final_score = final_score
    
    @register_method('equal_weight')
    def equal_weight(self):
        return [1.0 / self.length] * self.length

    @register_method('top_10_equal_weight')
    def top_10_equal_weight(self):
        k = min(10, self.length)
        top_k_indices = np.argpartition(self.final_score, -k)[-k:]
        weights = np.zeros(self.length)
        weights[top_k_indices] = 1.0 / k
        return weights
    
    def get_weights(self):
        """统一入口：根据 self.method 自动路由到注册的方法"""
        method_func = _method_registry.get(self.method)
        if method_func is None:
            raise ValueError(f"不支持的权重方法: {self.method}")
        return method_func(self)