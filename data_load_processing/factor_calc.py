import pandas as pd
import numpy as np
import os
from factor_lib.registry import FACTOR_MAP


_combination_registry = {}

def register_combination(combo_name, factors=None):
    """装饰器：注册因子组合方法
    combo_name: 组合名称（如 'hl'）
    factors: 这个组合需要用到哪些因子（如 ['hl'] 或 ['momentum_20', 'hl']）
    """
    def decorator(func):
        _combination_registry[combo_name] = (func, factors or [])
        return func
    return decorator


class FactorCalc:
    """因子计算类：滑动窗口方式读取 h5，逐日计算因子"""

    def __init__(self, stock_list: list, frequency: str = 'daily', fq: str = 'qfq'):
        self.stock_list = stock_list
        self.frequency = frequency
        self.fq = fq
        # 数据文件存放在 data_resource/ 目录下
        base_dir = os.path.join(os.path.dirname(__file__), 'data_resource')
        self.data_dir = base_dir

    def _file_path(self, stock: str) -> str:
        return os.path.join(
            self.data_dir,
            f'{stock}_{self.frequency}_{self.fq}.h5'
        )

    @register_combination('hl', factors=['hl'])
    def combin_hl(self, factor_values: dict) -> pd.Series:
        """hl 单因子组合，直接返回 hl 值"""
        return factor_values['hl']

    @register_combination('momentum_20', factors=['momentum_20'])
    def combin_momentum_20(self, factor_values: dict) -> pd.Series:
        return factor_values['momentum_20']

    @register_combination('momentum_hl', factors=['momentum_20', 'hl'])
    def combin_momentum_hl(self, factor_values: dict) -> pd.Series:
        """等权合成 momentum_20 + hl"""
        return 0.5 * factor_values['momentum_20'] + 0.5 * factor_values['hl']

    def compute(self, combination: str = 'hl') -> pd.DataFrame:
        """统一入口：滑动窗口计算因子，返回 final_table (index=date, columns=stock)"""
        # 1. 获取组合方法及所需因子列表
        entry = _combination_registry.get(combination)
        if entry is None:
            raise ValueError(
                f"不支持的因子组合: {combination}，可用: {list(_combination_registry.keys())}"
            )
        combo_func, factor_names = entry

        if not factor_names:
            raise ValueError(f"组合 '{combination}' 未声明依赖的因子")

        # 2. 查询每个因子的 MTW，取最大值
        factor_info = []
        max_mtw = 0
        for name in factor_names:
            if name not in FACTOR_MAP:
                raise ValueError(f"因子 '{name}' 未注册，可用: {list(FACTOR_MAP.keys())}")
            func, mtw = FACTOR_MAP[name]
            factor_info.append((name, func, mtw))
            if mtw > max_mtw:
                max_mtw = mtw

        # 3. 对每只股票滑动窗口计算
        all_results = []  # 收集 (date, stock, score)

        for stock in self.stock_list:
            fpath = self._file_path(stock)
            if not os.path.exists(fpath):
                print(f"⚠️ {stock} 文件不存在，跳过")
                continue

            try:
                # 先读全部 date 列，确定总行数和日期序列
                dates = pd.read_hdf(fpath, key='data', columns=['date'])
                nrows = len(dates)
                if nrows <= max_mtw:
                    print(f"⚠️ {stock} 数据行数({nrows})不足 max_mtw({max_mtw})，跳过")
                    continue
            except Exception as e:
                print(f"⚠️ {stock} 读取日期列失败: {e}")
                continue

            # 滑动窗口
            for t in range(max_mtw, nrows):
                # 只读 max_mtw+1 行
                window = pd.read_hdf(
                    fpath, key='data',
                    start=t - max_mtw,
                    stop=t + 1
                )
                # 计算每个因子
                day_values = {}
                for name, func, mtw in factor_info:
                    series = func(window)
                    day_values[name] = series.iloc[-1]

                # 组合得到今天得分
                today_score = combo_func(self, day_values)

                # 记录
                today_date = dates.iloc[t]['date']
                all_results.append({
                    'date': today_date,
                    'stock': stock,
                    'score': today_score
                })

        if not all_results:
            raise ValueError("没有成功计算出任何因子得分")

        # 4. 拼成 final_table: index=date, columns=stock
        result_df = pd.DataFrame(all_results)
        final_table = result_df.pivot(index='date', columns='stock', values='score')
        final_table.index.name = 'date'
        final_table.sort_index(inplace=True)

        return final_table

    def list_combinations(self):
        """查看所有已注册的组合方法及其依赖的因子"""
        return {k: v[1] for k, v in _combination_registry.items()}
